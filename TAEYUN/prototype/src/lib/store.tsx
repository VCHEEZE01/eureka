'use client';

/**
 * 프로토타입 전역 상태.
 * 백엔드가 없으므로 localStorage에 보관한다.
 *
 * 담당 범위: 로그인(F10), 리서치 범위(F02), 문제 선택·조합(F05),
 * 개인화 결과(F07), 즐겨찾기/보관함(F09).
 *
 * 모듈 수준 스토어 + useSyncExternalStore를 쓴다.
 * 이펙트에서 setState로 복원하면 마운트마다 연쇄 렌더가 생기므로
 * 스냅샷을 직접 읽어 첫 클라이언트 렌더에서 바로 복원된 값을 쓴다.
 */

import { useCallback, useSyncExternalStore } from 'react';
import {
  savedKey,
  type CombinedProblem,
  type PersonalizeRun,
  type SavedItem,
  type SavedKind,
  type SourceKind,
} from './types';

const STORAGE_KEY = 'eureka.prototype.v1';

export interface User {
  email: string;
  nickname: string;
}

interface State {
  user: User | null;
  /** F02에서 고른 수집 범위. null이면 아직 온보딩을 안 거쳤다. */
  scope: SourceKind[] | null;
  /** F05 조합을 위해 문제 탐색에서 체크한 문제들 */
  selectedProblemIds: string[];
  combined: CombinedProblem[];
  runs: PersonalizeRun[];
  saved: SavedItem[];
}

const EMPTY: State = {
  user: null,
  scope: null,
  selectedProblemIds: [],
  combined: [],
  runs: [],
  saved: [],
};

let state: State = EMPTY;
let loaded = false;
const listeners = new Set<() => void>();

function load(): State {
  if (typeof window === 'undefined') return EMPTY;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return EMPTY;
    return { ...EMPTY, ...(JSON.parse(raw) as Partial<State>) };
  } catch {
    // 저장값이 깨졌거나 접근이 막힌 경우 빈 상태로 시작한다.
    return EMPTY;
  }
}

function persist() {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // 시크릿 모드 등에서 쓰기가 막혀도 화면은 그대로 동작해야 한다.
  }
}

function set(next: Partial<State>) {
  state = { ...state, ...next };
  persist();
  listeners.forEach((fn) => fn());
}

function subscribe(fn: () => void) {
  if (!loaded) {
    state = load();
    loaded = true;
  }
  listeners.add(fn);
  return () => listeners.delete(fn);
}

function getSnapshot(): State {
  if (!loaded && typeof window !== 'undefined') {
    state = load();
    loaded = true;
  }
  return state;
}

/** 서버 렌더 시에는 항상 빈 상태. 하이드레이션 불일치를 막는다. */
function getServerSnapshot(): State {
  return EMPTY;
}

export function useStore() {
  const snapshot = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const login = useCallback((email: string, nickname: string) => {
    set({ user: { email, nickname } });
  }, []);

  const logout = useCallback(() => set({ user: null }), []);

  const setScope = useCallback((scope: SourceKind[]) => set({ scope }), []);

  const toggleProblemSelect = useCallback((id: string) => {
    const current = state.selectedProblemIds;
    set({
      selectedProblemIds: current.includes(id)
        ? current.filter((x) => x !== id)
        : [...current, id],
    });
  }, []);

  const clearProblemSelect = useCallback(() => set({ selectedProblemIds: [] }), []);

  const addCombined = useCallback((c: CombinedProblem) => {
    if (state.combined.some((x) => x.id === c.id)) return;
    set({ combined: [c, ...state.combined] });
  }, []);

  const addRun = useCallback((run: PersonalizeRun) => {
    const rest = state.runs.filter((r) => r.id !== run.id);
    set({ runs: [run, ...rest] });
  }, []);

  const toggleSave = useCallback(
    (item: Omit<SavedItem, 'key' | 'savedAt'>) => {
      const key = savedKey(item.kind, item.refId);
      const exists = state.saved.some((s) => s.key === key);
      set({
        saved: exists
          ? state.saved.filter((s) => s.key !== key)
          : [{ ...item, key, savedAt: new Date().toISOString() }, ...state.saved],
      });
    },
    [],
  );

  const isSaved = useCallback(
    (kind: SavedKind, refId: string) =>
      snapshot.saved.some((s) => s.key === savedKey(kind, refId)),
    [snapshot.saved],
  );

  return {
    ...snapshot,
    login,
    logout,
    setScope,
    toggleProblemSelect,
    clearProblemSelect,
    addCombined,
    addRun,
    toggleSave,
    isSaved,
  };
}

export function getCombined(id: string): CombinedProblem | undefined {
  return getSnapshot().combined.find((c) => c.id === id);
}

export function getRun(id: string): PersonalizeRun | undefined {
  return getSnapshot().runs.find((r) => r.id === id);
}
