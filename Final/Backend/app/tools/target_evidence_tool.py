"""Verify target labels against the same person's verbatim experience, without LLM calls."""
from __future__ import annotations

import json
import re
from hashlib import sha256

from app.schemas.collections import TargetProfile

POLICY = "evidence_v2"
_GENDERS = {"남자": "남성", "남성": "남성", "여자": "여성", "여성": "여성"}
_SELF = re.compile(r"(?:저는|제가|나는|내가|본인은|나이는|제\s*나이|저의\s*나이|저도|전\s)")
_OTHER = re.compile(r"(?:남자친구|여자친구|친구|남편|아내|오빠|언니|형|누나|동생|고객|환자|그분|그\s*남성|그\s*여성|아버지|어머니)(?:분)?(?:은|는|이|가|의)")


def profile_key(target: TargetProfile) -> str:
    return sha256(json.dumps(target.model_dump(), ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def grounded_quote(value: object, source: str, maximum: int = 400) -> str | None:
    if not isinstance(value, str):
        return None
    quote = normalized(value)
    return quote if 2 <= len(quote) <= maximum and quote in normalized(source) else None


def _age_band(number: int) -> str | None:
    if 10 <= number < 50:
        return f"{number // 10 * 10}대"
    return "50대 이상" if 50 <= number <= 120 else None


def _intro_tail(suffix: str) -> bool:
    match = re.match(r"(.{0,28}?)(?:입니다|인데|이고|이며|이라|이에요|예요|인\s*(?:저|나))", suffix)
    if not match:
        return False
    bridge = match.group(1)
    # A first-person subject does not make its object the person's identity.
    return not re.search(r"을|를|에게|한테|봤|보고|만나|돕|위한|대상|추천|모집|채용|친구|고객|환자|분(?:은|을|이|과|께)", bridge)


def self_attribute(value: str, source: str, field: str) -> bool:
    """An explicit narrator introduction, including numeric ages, is required."""
    if field == "gender":
        canonical = _GENDERS.get(value)
        if not canonical:
            return False
        pattern = re.compile(r"(?:남자|남성|여자|여성)(?!친구)")
    else:
        pattern = re.compile(r"(?<!\d)(\d{1,3})\s*(?:대|세|살)")
    for clause in re.split(r"[.!?\n]|(?:하지만|그런데)", source):
        for match in pattern.finditer(clause):
            observed = _GENDERS.get(match.group()) if field == "gender" else _age_band(int(match.group(1)))
            if observed != (_GENDERS.get(value) if field == "gender" else value):
                continue
            prefix, suffix = clause[:match.start()], clause[match.end():]
            own, others = list(_SELF.finditer(prefix)), list(_OTHER.finditer(prefix))
            last_self = own[-1].end() if own else -1
            if others and others[-1].start() >= last_self:
                continue
            if not _intro_tail(suffix):
                # "제 나이는 23살" is also an explicit self age statement.
                if not (field == "age" and own and re.search(r"(?:제|저의|내|나이는).*나이|나이는", prefix) and not suffix.strip()):
                    continue
            if own and len(prefix) - last_self <= 35:
                return True
            # Self-introductions with omitted "저는": "23살 남자인데".
            if not others and (not prefix.strip() or re.fullmatch(r"\s*(?:나이는\s*)?\d+(?:대|세|살)\s*(?:초반|중반|후반)?\s*", prefix)):
                return True
    return False


def qa_mixed(source: str, url: str) -> bool:
    return "kin.naver.com" in url and bool(re.search(
        r"질문자님|(?:안녕하세요[.\s]*)[^.!?]{0,45}(?:상담의|전문의|답변)|불편했겠|느껴지셨|도움이\s*되셨|답변\s*드립니다", source))


def verify_target(row: dict, source: str, target: TargetProfile, *, experience_type: str, experience: str | None) -> dict:
    fields = {key: value for key, value in target.model_dump().items() if value}
    statuses = {field: "unconfirmed" for field in fields}
    quotes, values = {}, {}
    raw_quotes = row.get("target_evidence") if isinstance(row.get("target_evidence"), dict) else {}
    raw_values = row.get("target_values") if isinstance(row.get("target_values"), dict) else {}
    declared = row.get("target_field_status") if isinstance(row.get("target_field_status"), dict) else {}
    if experience_type == "self" and experience:
        for field, expected in fields.items():
            quote = grounded_quote(raw_quotes.get(field), source, 300)
            value = raw_values.get(field)
            if not quote or quote not in experience or not isinstance(value, str) or not value.strip():
                continue
            value = value.strip()
            if field in {"age", "gender"}:
                if not self_attribute(value, quote, field):
                    continue
                observed = _GENDERS.get(value) if field == "gender" else value
                if field == "age" and value not in {"10대", "20대", "30대", "40대", "50대 이상"}:
                    continue
                if not observed:
                    continue
                statuses[field] = "confirmed" if observed == expected else "conflict"
            else:
                # Job/place labels must be present in the same first-person experience.
                # Never turn a job example in an answer into the questioner's identity.
                if not _SELF.search(quote) and not re.search(r"(?:인데|로\s*일|에서\s*(?:일|근무|생활|살|작업))", quote):
                    continue
                if _OTHER.search(quote):
                    continue
                key = normalized(value).casefold()
                if key not in {normalized(token).casefold() for token in expected}:
                    continue
                # Exact nominal boundary: 의사 != 수의사, 집 != 편집실.
                nominal = re.search(r"(?<![가-힣A-Za-z])" + re.escape(value) + r"(?=$|[ ,.!?]|(?:에서|으로|로|인|이|은|는|을|를|에|와|과))", quote, re.IGNORECASE)
                if not nominal:
                    continue
                tail = quote[nominal.end():]
                if field == "jobs" and not re.match(r"(?:인|이|으로|로|\s*(?:업무|일|직무|담당|근무))", tail):
                    continue
                if field == "places" and not re.match(r"(?:에서|에|\s*(?:안|내부|내|근처|밖))", tail):
                    continue
                matches = True
                if not matches:
                    # Different workplaces/jobs can coexist; an unrelated mention is not a contradiction.
                    continue
                if declared.get(field) != "confirmed":
                    continue
                statuses[field] = "confirmed"
            quotes[field], values[field] = quote, value
    overall = "conflict" if "conflict" in statuses.values() else "confirmed" if all(value == "confirmed" for value in statuses.values()) else "unconfirmed"
    return {"target_status": overall, "target_field_status": statuses, "target_evidence": quotes,
            "target_values": values, "target_profile_key": profile_key(target), "target_policy": POLICY}
