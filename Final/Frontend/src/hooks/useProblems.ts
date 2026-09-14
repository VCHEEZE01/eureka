
'use client';
import { useEffect, useState } from 'react';
import { DATA_MODE, fetchProblem, fetchProblems } from '@/api/client';
import type { Problem } from '@/api/types';
import { problems as demoProblems } from '@/data/mock';

export function useProblems() {
  const [problems, setProblems] = useState<Problem[]>(DATA_MODE === 'demo' ? demoProblems : []);
  const [loading, setLoading] = useState(DATA_MODE !== 'demo');
  const [error, setError] = useState('');
  useEffect(() => {
    if (DATA_MODE === 'demo') return;
    let active = true;
    fetchProblems().then(data => { if (active) setProblems(data); }).catch(() => { if (active) setError('문제 목록을 불러오지 못했습니다. API 연결을 확인한 후 새로고침해 주세요.'); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);
  return { problems, loading, error };
}

export function useProblem(id: string) {
  const [state, setState] = useState<{id: string; problem?: Problem; loading: boolean; error: string}>({id, loading: DATA_MODE !== 'demo', error: '', problem: DATA_MODE === 'demo' ? demoProblems.find(p => p.id === id) : undefined});
  useEffect(() => {
    if (DATA_MODE === 'demo') return;
    let active = true;
    fetchProblem(id).then(problem => { if (active) setState({id, problem, loading: false, error: ''}); }).catch(error => { if (active) setState({id, loading: false, error: error instanceof Error ? error.message : '데이터를 불러오지 못했습니다.'}); });
    return () => { active = false; };
  }, [id]);
  if (DATA_MODE === 'demo') return {problem: demoProblems.find(p => p.id === id), loading: false, error: ''};
  return state.id === id ? state : {problem: undefined, loading: true, error: ''};
}
