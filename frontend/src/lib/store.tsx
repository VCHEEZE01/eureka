'use client';

/**
 * 프로토타입용 클라이언트 전역 상태.
 * 로그인(F08), 즐겨찾기/보관함(F07), 개인화 결과(F05), A/B/C 변형을 담당한다.
 * 백엔드가 아직 없으므로 localStorage에 보관한다.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
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

interface Store extends PersistedState {
  /** localStorage 복원이 끝났는지. 서버/클라이언트 마크업 불일치를 막는 데 쓴다. */
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

function readStorage(): PersistedState {
  if (typeof window === 'undefined') return EMPTY_STATE;
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

export function StoreProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<PersistedState>(EMPTY_STATE);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const restored = readStorage();
    // ?v=B 처럼 URL로 변형을 지정하면 저장값보다 우선한다. (실험 링크 공유용)
    const fromUrl = new URLSearchParams(window.location.search)
      .get('v')
      ?.toUpperCase() as Variant | undefined;
    setState(
      fromUrl && VARIANTS.includes(fromUrl)
        ? { ...restored, variant: fromUrl }
        : restored,
    );
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      // 저장 실패(용량 초과/프라이빗 모드)는 프로토타입에서 무시한다.
    }
  }, [state, hydrated]);

  const setVariant = useCallback((variant: Variant) => {
    setState((prev) => ({ ...prev, variant }));
  }, []);

  const login = useCallback((email: string, nickname?: string) => {
    setState((prev) => ({
      ...prev,
      user: { email, nickname: nickname || email.split('@')[0] },
    }));
  }, []);

  const logout = useCallback(() => {
    setState((prev) => ({ ...prev, user: null }));
  }, []);

  const isSaved = useCallback(
    (kind: SavedKind, refId: string) =>
      state.saved.some((item) => item.key === savedKey(kind, refId)),
    [state.saved],
  );

  const toggleSave = useCallback(
    (item: Omit<SavedItem, 'key' | 'savedAt'>) => {
      let handled = false;
      setState((prev) => {
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
    setState((prev) => ({ ...prev, runs: [run, ...prev.runs].slice(0, 20) }));
  }, []);

  const getRun = useCallback(
    (id: string) => state.runs.find((run) => run.id === id),
    [state.runs],
  );

  const value = useMemo<Store>(
    () => ({
      ...state,
      hydrated,
      variantSpec: VARIANT_SPECS[state.variant],
      setVariant,
      login,
      logout,
      isSaved,
      toggleSave,
      addRun,
      getRun,
    }),
    [state, hydrated, setVariant, login, logout, isSaved, toggleSave, addRun, getRun],
  );

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

export function useStore(): Store {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error('useStore must be used within <StoreProvider>');
  return ctx;
}
