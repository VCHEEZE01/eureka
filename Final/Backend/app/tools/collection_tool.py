"""타겟 수집 실행 저장·중복 방지·독립 worker 시작. GET은 worker를 시작하지 않는다."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from app.config.settings import settings
from app.schemas.collections import CollectionCounts, CollectionLimits, CollectionRun, TargetProfile
from app.tools.target_query_tool import PLAN_VERSION, build_target_queries, coverage_for, target_warnings

_ACTIVE = {"queued", "running"}
_processes: dict[str, subprocess.Popen] = {}


class CollectionStoreError(ValueError):
    pass


class CollectionRequestError(ValueError):
    pass


class CollectionBusyError(ValueError):
    def __init__(self, run_id: str):
        self.run_id = run_id
        super().__init__("다른 타겟을 수집하고 있습니다. 진행 중인 실행이 끝난 뒤 다시 요청하세요")


def now() -> datetime:
    return datetime.now(timezone.utc)


def run_dir(run_id: str) -> Path:
    if not re.fullmatch(r"col-[0-9a-f]{24}", run_id):
        raise CollectionStoreError("올바르지 않은 수집 실행 ID입니다")
    return Path(settings.COLLECTIONS_DIR) / run_id


@contextmanager
def store_lock():
    root = Path(settings.COLLECTIONS_DIR)
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".manager.lock").open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        yield


def _read(run_id: str) -> Optional[dict]:
    path = run_dir(run_id) / "run.json"
    if not path.exists():
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        public = CollectionRun.model_validate(record)
        if public.id != run_id or record.get("schema_version") != 1:
            raise ValueError("run mismatch")
        return record
    except (ValueError, TypeError, OSError) as exc:
        raise CollectionStoreError("수집 실행 기록이 손상되었습니다") from exc


def _write(record: dict) -> None:
    path = run_dir(record["id"]) / "run.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    record["updated_at"] = now().isoformat()
    fd, temp = tempfile.mkstemp(prefix=".run-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def update_run(run_id: str, **changes) -> CollectionRun:
    with store_lock():
        record = _read(run_id)
        if record is None:
            raise CollectionStoreError("수집 실행을 찾을 수 없습니다")
        # 강제 종료를 이미 확인한 GET과 늦게 도착한 worker 쓰기가 상태를 되돌리지 않는다.
        if record["status"] in {"completed", "failed"}:
            return _public_run(record)
        record.update(changes)
        _write(record)
        return _public_run(record)


def _worker_lock_held(record: dict) -> bool:
    path = run_dir(record["id"]) / "worker.lock"
    if not path.exists():
        return False
    with path.open("r+") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return False


def _is_alive(record: dict) -> bool:
    tracked = _processes.get(record["id"])
    if tracked is not None:
        return tracked.poll() is None
    if record.get("worker_liveness_policy") == "file_lock_v1":
        if _worker_lock_held(record):
            return True
        # 시작 직후 Python imports 동안만 짧은 유예를 둔다. 상태가 failed면 늦게 뜬 worker도 실행하지 않는다.
        return (record["status"] == "queued"
                and (now() - datetime.fromisoformat(record["created_at"])).total_seconds() < 10)
    pid = record.get("worker_pid")
    if not isinstance(pid, int) or pid < 1:
        return False
    # 재시작 뒤 PID 재사용을 살아 있는 원래 worker로 오인하지 않는다.
    try:
        command = subprocess.run(["ps", "-p", str(pid), "-o", "command="],
                                 capture_output=True, text=True, timeout=2, check=False)
    except (OSError, subprocess.TimeoutExpired):
        # 일시적인 관측 실패로 원래 작업을 재시작하지 않는다. hard timeout이 따로 있다.
        return True
    return (command.returncode == 0 and "app.workers.collection_worker" in command.stdout
            and record["id"] in command.stdout)



def _terminate_timed_out_worker(record: dict) -> bool:
    """제한시간 초과 후 같은 worker의 종료를 확인하기 전에는 실행 슬롯을 풀지 않는다."""
    tracked = _processes.get(record["id"])
    if tracked is not None:
        if tracked.poll() is None:
            tracked.terminate()
            try:
                tracked.wait(timeout=2)
            except subprocess.TimeoutExpired:
                tracked.kill()
                tracked.wait(timeout=2)
        return tracked.poll() is not None
    if record.get("worker_liveness_policy") == "file_lock_v1":
        if not _worker_lock_held(record):
            return True
        try:
            owner = json.loads((run_dir(record["id"]) / "worker.lock").read_text(encoding="utf-8"))
            pid = owner.get("pid")
            if owner.get("run_id") != record["id"] or not isinstance(pid, int) or pid < 1:
                return False
            os.kill(pid, signal.SIGTERM)
            return not _worker_lock_held(record)
        except ProcessLookupError:
            return True
        except (OSError, ValueError):
            return False
    pid = record.get("worker_pid")
    if not isinstance(pid, int) or pid < 1:
        return True
    try:
        command = subprocess.run(["ps", "-p", str(pid), "-o", "command="],
                                 capture_output=True, text=True, timeout=2, check=False)
        if command.returncode != 0:
            return True
        if "app.workers.collection_worker" not in command.stdout or record["id"] not in command.stdout:
            return True  # PID가 재사용됐다. 다른 프로세스를 종료하지 않는다.
        os.kill(pid, signal.SIGTERM)
        check = subprocess.run(["ps", "-p", str(pid), "-o", "command="],
                               capture_output=True, text=True, timeout=2, check=False)
        return check.returncode != 0 or record["id"] not in check.stdout
    except ProcessLookupError:
        return True
    except (OSError, subprocess.TimeoutExpired):
        return False  # 관측 실패는 종료 확인이 아니다. 다음 상태 조회에서 재확인한다.

def _reconcile(record: dict) -> dict:
    if record["status"] not in _ACTIVE:
        return record
    elapsed = (now() - datetime.fromisoformat(record["created_at"])).total_seconds()
    if elapsed > record["limits"]["timeout_seconds"] + 15:
        # worker 자체의 alarm과 별개로 살아 있는 같은 worker가 남았는지도 확인한다.
        if not _terminate_timed_out_worker(record):
            record["message"] = "수집 제한 시간이 지나 작업 종료를 확인하고 있습니다"
            _write(record)
            return record
        error = "수집 실행 제한 시간을 넘었습니다. 완료되지 않은 결과는 공개되지 않았습니다"
    elif not _is_alive(record):
        error = "수집 작업이 중단되었습니다. 서버 또는 worker 재시작 후 다시 실행할 수 있습니다"
    else:
        return record
    record.update(status="failed", stage="failed", message=error, error=error)
    _write(record)
    return record


def _public_run(record: dict) -> CollectionRun:
    """현재 계획과 재개 가능 여부는 응답에서만 계산해 과거 기록을 보존한다."""
    public = CollectionRun.model_validate(record)
    public.current_plan_version = PLAN_VERSION
    public.can_resume = (public.status in {"completed", "failed"} and public.has_more
                         and public.plan_version == PLAN_VERSION and public.target_match_policy == "evidence_v2"
                         and record.get("fingerprint") == _fingerprint(public.target))
    return public


def get_run(run_id: str) -> Optional[CollectionRun]:
    # 존재하지 않는 GET 때문에 디렉터리를 만들지 않는다.
    if not (run_dir(run_id) / "run.json").exists():
        return None
    with store_lock():
        record = _read(run_id)
        return _public_run(_reconcile(record)) if record else None


def _fingerprint(target: TargetProfile) -> str:
    return hashlib.sha256((PLAN_VERSION + ":" + target.model_dump_json()).encode("utf-8")).hexdigest()


def configuration_error(queries) -> Optional[str]:
    if settings.LLM_DRY_RUN or settings.LLM_PROVIDER == "echo":
        return "실제 수집에는 실제 LLM 설정이 필요합니다. LLM_DRY_RUN=false로 설정하세요"
    required = {}
    providers = {q.provider for q in queries}
    if "naver" in providers:
        required.update(NAVER_CLIENT_ID=settings.NAVER_CLIENT_ID, NAVER_CLIENT_SECRET=settings.NAVER_CLIENT_SECRET)
    if "kakao" in providers:
        required["KAKAO_REST_API_KEY"] = settings.KAKAO_REST_API_KEY
    if settings.LLM_PROVIDER == "gemini":
        required.update(GEMINI_API_KEY=settings.GEMINI_API_KEY, GEMINI_MODEL=settings.GEMINI_MODEL)
    else:
        required.update(LLM_API_KEY=settings.LLM_API_KEY, LLM_BASE_URL=settings.LLM_BASE_URL, LLM_MODEL=settings.LLM_MODEL)
    missing = [name for name, value in required.items() if not value]
    return "실제 호출 설정이 비어 있습니다: " + ", ".join(missing) if missing else None


def _worker_environment(run_id: str) -> dict[str, str]:
    # 환경 구성은 config의 살아 있는 설정을 직렬화해 전달한다. 서버 설정을 제자리에서 바꾸지 않는다.
    from app.config.settings import child_process_environment
    env = child_process_environment()
    folder = run_dir(run_id).resolve()
    env.update(CORPUS_DIR=str(folder / "corpus"), PROBLEMS_DIR=str(folder / "private-problems"),
               COLLECTIONS_DIR=str(Path(settings.COLLECTIONS_DIR).resolve()),
               SEARCH_QUOTA_DIR=str(Path(settings.SEARCH_QUOTA_DIR or settings.CORPUS_DIR).resolve()),
               COLLECT_MAX_PAGES="1", COLLECT_PER_QUERY_LIMIT=str(settings.COLLECTION_ITEMS_PER_QUERY),
               MAX_LLM_ITEMS=str(settings.COLLECTION_JUDGE_BUDGET),
               CLUSTER_BACKEND="tfidf")
    return env


def _launch_worker(run_id: str) -> int:
    log_path = run_dir(run_id) / "worker.log"
    with log_path.open("a", encoding="utf-8") as log:
        proc = subprocess.Popen(
            [sys.executable, "-m", "app.workers.collection_worker", run_id],
            cwd=Path(__file__).resolve().parents[2], env=_worker_environment(run_id),
            stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True,
        )
    _processes[run_id] = proc
    return proc.pid


def create_run(target: TargetProfile, *, resume_from: Optional[str] = None) -> CollectionRun:
    fingerprint = _fingerprint(target)
    with store_lock():
        records = []
        for path in sorted(Path(settings.COLLECTIONS_DIR).glob("col-*/run.json")):
            record = _read(path.parent.name)
            if record:
                records.append(_reconcile(record))
        parent = None
        if resume_from:
            if not re.fullmatch(r"col-[0-9a-f]{24}", resume_from):
                raise CollectionRequestError("이어 수집할 실행 ID가 올바르지 않습니다")
            parent = _read(resume_from)
            if parent is None:
                raise CollectionRequestError("이어 수집할 실행을 찾을 수 없습니다")
            if (parent.get("fingerprint") != fingerprint or parent.get("plan_version") != PLAN_VERSION
                    or parent.get("target_match_policy") != "evidence_v2"):
                raise CollectionRequestError("같은 타겟과 현재 수집 계획의 실행만 이어서 수집할 수 있습니다")
            if parent["status"] in _ACTIVE:
                raise CollectionBusyError(parent["id"])
            if not parent.get("has_more"):
                raise CollectionRequestError("이 탐색 계획의 남은 수집 범위가 없습니다")
        for record in reversed(records):
            if record.get("fingerprint") != fingerprint:
                continue
            if resume_from:
                # 실패한 자식이 있다면 그 자식 ID에서 다시 이어 간다. 같은 버튼의 중복 POST는 같은 자식이다.
                reusable = record.get("resume_from") == resume_from
            else:
                recent = (now() - datetime.fromisoformat(record["updated_at"])).total_seconds() < settings.COLLECTION_REUSE_SEC
                reusable = not record.get("resume_from") and (record["status"] in _ACTIVE or (record["status"] == "completed" and recent))
            if reusable:
                public = _public_run(record)
                public.reused = True
                return public
        active = next((r for r in records if r["status"] in _ACTIVE), None)
        if active:
            raise CollectionBusyError(active["id"])
        completed_ids = list(parent.get("completed_query_ids", [])) if parent else []
        topics = list(parent.get("searched_topic_ids", [])) if parent else []
        intents = list(parent.get("searched_intents", [])) if parent else []
        queries = build_target_queries(target, completed_ids=completed_ids)
        timestamp = now()
        run_id = f"col-{uuid4().hex[:24]}"
        limits = CollectionLimits(
            search_queries=len(queries), search_http_attempts=len(queries) * 3,
            collected_items=len(queries) * settings.COLLECTION_ITEMS_PER_QUERY,
            items_per_query=settings.COLLECTION_ITEMS_PER_QUERY, items_per_category=settings.COLLECTION_JUDGE_PER_CATEGORY,
            judged_items=settings.COLLECTION_JUDGE_BUDGET, problem_candidates=settings.COLLECTION_PROBLEM_BUDGET,
            llm_logical_calls=settings.COLLECTION_LLM_CALL_BUDGET, llm_http_attempts=settings.COLLECTION_LLM_CALL_BUDGET * 2 * (settings.LLM_MAX_RETRIES + 1),
            timeout_seconds=settings.COLLECTION_TIMEOUT_SEC,
        )
        run = CollectionRun(
            id=run_id, status="queued", stage="queued", message="전체 주제와 타겟 맥락에서 이번 회차의 수집을 준비합니다",
            target=target, queries=queries, counts=CollectionCounts(queries_total=len(queries)), warnings=target_warnings(target),
            limits=limits, created_at=timestamp, updated_at=timestamp, target_match_policy="evidence_v2",
            plan_version=PLAN_VERSION, current_plan_version=PLAN_VERSION, series_id=parent.get("series_id", parent["id"]) if parent else run_id,
            resume_from=resume_from, round_index=parent.get("round_index", 1) + 1 if parent else 1,
            coverage=coverage_for(target, completed_ids=completed_ids, topic_ids=topics, intents=intents), has_more=True,
            cumulative_counts=parent.get("cumulative_counts", {}) if parent else CollectionCounts(),
            problems=parent.get("problems", []) if parent else [], reviews=parent.get("reviews", {}) if parent else {},
            review_candidates=parent.get("review_candidates", []) if parent else [],
        )
        record = run.model_dump(mode="json")
        record.update(schema_version=1, fingerprint=fingerprint, worker_pid=None, worker_liveness_policy="file_lock_v1",
                      completed_query_ids=completed_ids, searched_topic_ids=topics, searched_intents=intents,
                      processed_raw_ids=parent.get("processed_raw_ids", []) if parent else [],
                      generated_candidate_ids=parent.get("generated_candidate_ids", []) if parent else [],
                      pending_candidate_ids=parent.get("pending_candidate_ids", []) if parent else [])
        error = configuration_error(queries)
        if error:
            record.update(status="failed", stage="failed", message=error, error=error, stop_reason="failed")
            _write(record)
            return _public_run(record)
        _write(record)
        try:
            record["worker_pid"] = _launch_worker(run.id)
        except OSError:
            error = "수집 worker를 시작하지 못했습니다. 서버 실행 환경을 확인하세요"
            record.update(status="failed", stage="failed", message=error, error=error, stop_reason="failed")
        _write(record)
        return _public_run(record)


def prepare_corpus_snapshot(run: CollectionRun) -> None:
    """같은 탐색의 부모 원문·판정을 새 실행에 복사한다. 부모 파일은 읽기만 한다."""
    if not run.resume_from:
        return
    parent = _read(run.resume_from)
    if (parent is None or parent.get("fingerprint") != _fingerprint(run.target)
            or parent.get("plan_version") != run.plan_version or parent["status"] in _ACTIVE):
        raise CollectionRequestError("누적할 실행의 타겟·계획·종료 상태가 일치하지 않습니다")
    source = run_dir(run.resume_from) / "corpus"
    destination = run_dir(run.id) / "corpus"
    for kind in ("raw", "judgements"):
        origin = source / kind
        if origin.exists():
            target_dir = destination / kind
            if target_dir.exists():
                raise CollectionStoreError("새 실행의 누적 저장소가 이미 존재합니다")
            shutil.copytree(origin, target_dir)
            if kind == "judgements":
                # 실패/누락 판정은 부모에 보존하되 자식에서는 재판별한다.
                # 첫 레코드를 읽는 근거 조회가 과거 degraded 판정을 재사용하지 않게 한다.
                processed = set(parent.get("processed_raw_ids", []))
                for path in target_dir.rglob("*.jsonl"):
                    rows = [line for line in path.read_text(encoding="utf-8").splitlines()
                            if line.strip() and json.loads(line).get("raw_item_id") in processed]
                    path.write_text("".join(line + "\n" for line in rows), encoding="utf-8")
