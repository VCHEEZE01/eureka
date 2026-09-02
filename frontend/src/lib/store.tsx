'use client';

/**
 * 프로토타입용 클라이언트 전역 상태.
 * 로그인(F08), 즐겨찾기/보관함(F07), 개인화 결과(F05), A/B/C 변형을 담당한다.
 * 백엔드가 아직 없으므로 localStorage에 보관한다.
 *
 * 모듈 수준 외부 스토어 + useSyncExternalStore 조합을 쓴다.
 * 이펙트에서 setState로 복원하면 마운트마다 연쇄 렌더가 발생하므로,
 * 스냅샷을 직접 읽어 첫 클라이언트 렌더에서 바로 복원된 값을 쓴다.
 */

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useSyncExternalStore,
  type ReactNode,
} from 'react';
import {
  savedKey,
  VARIANT_SPECS,
  VARIANTS,
  type PersonalizationRun,
  type SavedItem,
  type SavedKind,
  type Variant,
  type VariantSpec,
} from './types';

const STORAGE_KEY = 'eureka.v1';

interface User {
  email: string;
  nickname: string;
}

interface PersistedState {
  user: User | null;
  saved: SavedItem[];
  runs: PersonalizationRun[];
  variant: Variant;
}

const EMPTY_STATE: PersistedState = {
  user: null,
  saved: [],
  runs: [],
  variant: 'A',
};

/* ── 외부 스토어 ───────────────────────────────────────────────── */

let state: PersistedState = EMPTY_STATE;
let loaded = false;
const listeners = new Set<() => void>();

function readStorage(): PersistedState {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return EMPTY_STATE;
    const parsed = JSON.parse(raw) as Partial<PersistedState>;
    return {
      user: parsed.user ?? null,
      saved: Array.isArray(parsed.saved) ? parsed.saved : [],
      runs: Array.isArray(parsed.runs) ? parsed.runs : [],
      variant:
        parsed.variant && VARIANTS.includes(parsed.variant) ? parsed.variant : 'A',
    };
  } catch {
    // 손상된 값이면 초기 상태로 되돌린다.
    return EMPTY_STATE;
  }
}

/** 최초 클라이언트 접근 시 한 번만 localStorage와 URL에서 상태를 복원한다. */
function ensureLoaded() {
  if (loaded || typeof window === 'undefined') return;
  loaded = true;
  const restored = readStorage();
  // ?v=B 처럼 URL로 변형을 지정하면 저장값보다 우선한다. (실험 링크 공유용)
  const fromUrl = new URLSearchParams(window.location.search)
    .get('v')
    ?.toUpperCase() as Variant | undefined;
  state =
    fromUrl && VARIANTS.includes(fromUrl)
      ? { ...restored, variant: fromUrl }
      : restored;
}

function getSnapshot(): PersistedState {
  ensureLoaded();
  return state;
}

/** 서버 렌더에서는 항상 초기 상태를 쓴다. hydration 불일치를 막는다. */
function getServerSnapshot(): PersistedState {
  return EMPTY_STATE;
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function update(updater: (prev: PersistedState) => PersistedState) {
  ensureLoaded();
  const next = updater(state);
  if (next === state) return;
  state = next;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // 저장 실패(용량 초과/프라이빗 모드)는 프로토타입에서 무시한다.
  }
  listeners.forEach((listener) => listener());
}

/* ── React 바인딩 ──────────────────────────────────────────────── */

interface Store extends PersistedState {
  /** 클라이언트에서 복원이 끝났는지. 서버 마크업과의 불일치를 막는 데 쓴다. */
  hydrated: boolean;
  variantSpec: VariantSpec;
  setVariant: (variant: Variant) => void;
  login: (email: string, nickname?: string) => void;
  logout: () => void;
  isSaved: (kind: SavedKind, refId: string) => boolean;
  /** 저장/해제 토글. 로그인 상태가 아니면 false를 반환한다. */
  toggleSave: (item: Omit<SavedItem, 'key' | 'savedAt'>) => boolean;
  addRun: (run: PersonalizationRun) => void;
  getRun: (id: string) => PersonalizationRun | undefined;
}

const StoreContext = createContext<Store | null>(null);

export function StoreProvider({ children }: { children: ReactNode }) {
  const snapshot = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const hydrated = useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );

  const setVariant = useCallback((variant: Variant) => {
    update((prev) => ({ ...prev, variant }));
  }, []);

  const login = useCallback((email: string, nickname?: string) => {
    update((prev) => ({
      ...prev,
      user: { email, nickname: nickname || email.split('@')[0] },
    }));
  }, []);

  const logout = useCallback(() => {
    update((prev) => ({ ...prev, user: null }));
  }, []);

  const isSaved = useCallback(
    (kind: SavedKind, refId: string) =>
      snapshot.saved.some((item) => item.key === savedKey(kind, refId)),
    [snapshot.saved],
  );

  const toggleSave = useCallback(
    (item: Omit<SavedItem, 'key' | 'savedAt'>) => {
      let handled = false;
      update((prev) => {
        if (!prev.user) return prev; // F07: 저장은 로그인 필요
        handled = true;
        const key = savedKey(item.kind, item.refId);
        const exists = prev.saved.some((s) => s.key === key);
        return {
          ...prev,
          saved: exists
            ? prev.saved.filter((s) => s.key !== key)
            : [{ ...item, key, savedAt: new Date().toISOString() }, ...prev.saved],
        };
      });
      return handled;
    },
    [],
  );

  const addRun = useCallback((run: PersonalizationRun) => {
    update((prev) => ({ ...prev, runs: [run, ...prev.runs].slice(0, 20) }));
  }, []);

  const getRun = useCallback(
    (id: string) => snapshot.runs.find((run) => run.id === id),
    [snapshot.runs],
  );

  const value = useMemo<Store>(
    () => ({
      ...snapshot,
      hydrated,
      variantSpec: VARIANT_SPECS[snapshot.variant],
      setVariant,
      login,
      logout,
      isSaved,
      toggleSave,
      addRun,
      getRun,
    }),
    [snapshot, hydrated, setVariant, login, logout, isSaved, toggleSave, addRun, getRun],
  );

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

export function useStore(): Store {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error('useStore must be used within <StoreProvider>');
  return ctx;
}
