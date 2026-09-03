'use client';

/**
 * F05 초개인화 — 요청 폼.
 * `?problem=<id>`로 기준 문제를 자동 적용한다. 개인화는 로그인이 필요하므로
 * 비로그인 상태에서는 폼 대신 로그인 안내를 보여준다.
 */

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useMemo, useState, type FormEvent } from 'react';
import { Button, ButtonLink, Card, SectionTitle } from '@/components/ui';
import { getAllProblems, getProblem } from '@/lib/data';
import { generatePersonalizedIdeas, newRunId } from '@/lib/personalize';
import { useStore } from '@/lib/store';
import {
  EXTRA_MAX_LENGTH,
  RESOURCES,
  SERVICE_FORMS,
  TARGETS,
  type PersonalizationInput,
  type PersonalizationRun,
  type Resource,
  type ServiceForm,
  type Target,
} from '@/lib/types';

function isServiceForm(value: string | null): value is ServiceForm {
  return !!value && (SERVICE_FORMS as readonly string[]).includes(value);
}
function isTarget(value: string | null): value is Target {
  return !!value && (TARGETS as readonly string[]).includes(value);
}
function isResource(value: string | null): value is Resource {
  return !!value && (RESOURCES as readonly string[]).includes(value);
}

export default function PersonalizePage() {
  return (
    <Suspense fallback={<PersonalizeFallback />}>
      <PersonalizeContent />
    </Suspense>
  );
}

function PersonalizeFallback() {
  return (
    <div className="space-y-6">
      <SectionTitle title="초개인화" description="조건을 불러오는 중입니다…" />
      <Card className="h-64 animate-pulse">
        <span className="sr-only">불러오는 중</span>
      </Card>
    </div>
  );
}

function PersonalizeContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, hydrated, addRun } = useStore();

  const problemParam = searchParams.get('problem');
  const queryProblem = problemParam ? getProblem(problemParam) : undefined;
  const allProblems = useMemo(() => getAllProblems(), []);

  const [problemId, setProblemId] = useState(queryProblem?.id ?? '');
  const [serviceForm, setServiceForm] = useState<ServiceForm>(
    isServiceForm(searchParams.get('serviceForm'))
      ? (searchParams.get('serviceForm') as ServiceForm)
      : SERVICE_FORMS[0],
  );
  const [target, setTarget] = useState<Target>(
    isTarget(searchParams.get('target'))
      ? (searchParams.get('target') as Target)
      : TARGETS[0],
  );
  const [resource, setResource] = useState<Resource>(
    isResource(searchParams.get('resource'))
      ? (searchParams.get('resource') as Resource)
      : RESOURCES[0],
  );
  const [extra, setExtra] = useState(searchParams.get('extra') ?? '');

  const nextPath = `/personalize${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  if (!hydrated) {
    return <PersonalizeFallback />;
  }

  if (!user) {
    return (
      <div className="space-y-6">
        <SectionTitle
          title="초개인화"
          description="내 조건에 맞게 아이디어를 좁혀 봅니다."
        />
        <Card className="text-center">
          <p className="font-semibold">개인화는 로그인이 필요합니다</p>
          <p className="kr-text mx-auto mt-2 max-w-md text-sm text-muted">
            만들고 싶은 형태·타깃·리소스를 반영한 맞춤 아이디어와 저장 기능은
            로그인한 사용자만 이용할 수 있습니다.
          </p>
          <div className="mt-5 flex justify-center">
            <ButtonLink href={`/login?next=${encodeURIComponent(nextPath)}`}>
              로그인하고 계속하기
            </ButtonLink>
          </div>
        </Card>
      </div>
    );
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!problemId) return;

    const input: PersonalizationInput = {
      problemId,
      serviceForm,
      target,
      resource,
      extra: extra.trim() ? extra.trim() : undefined,
    };

    const run: PersonalizationRun = {
      id: newRunId(input),
      createdAt: new Date().toISOString(),
      input,
      ideas: generatePersonalizedIdeas(input),
    };

    addRun(run);
    router.push(`/personalize/${run.id}`);
  }

  return (
    <div className="space-y-6">
      <SectionTitle
        title="초개인화"
        description="만들고 싶은 형태·타깃·리소스를 알려주면 그 조건에 맞게 아이디어를 다시 구성합니다."
      />

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <fieldset>
            <legend className="text-sm font-semibold">기준 문제</legend>
            {queryProblem ? (
              <div className="kr-text mt-3 rounded-xl bg-surface-muted px-4 py-3 text-sm">
                <span className="font-semibold">{queryProblem.title}</span>
                <p className="mt-1 text-muted">{queryProblem.oneLiner}</p>
                <p className="mt-2 text-xs text-muted">
                  이 문제를 기준으로 자동 적용됩니다.{' '}
                  <Link href={`/problems/${queryProblem.id}`} className="text-brand hover:underline">
                    문제 상세 보기
                  </Link>
                </p>
              </div>
            ) : (
              <div className="mt-3 space-y-2">
                {problemParam && (
                  <p className="kr-text text-sm text-muted">
                    &quot;{problemParam}&quot; 문제를 찾을 수 없어 아래에서 직접 선택해
                    주세요.
                  </p>
                )}
                <label htmlFor="problemId" className="sr-only">
                  기준 문제 선택
                </label>
                <select
                  id="problemId"
                  value={problemId}
                  onChange={(e) => setProblemId(e.target.value)}
                  required
                  className="w-full rounded-xl border border-border bg-surface px-3 py-2.5 text-sm"
                >
                  <option value="" disabled>
                    문제를 선택하세요
                  </option>
                  {allProblems.map((problem) => (
                    <option key={problem.id} value={problem.id}>
                      {problem.title}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </fieldset>
        </Card>

        <Card>
          <fieldset>
            <legend className="text-sm font-semibold">만들고 싶은 형태</legend>
            <div className="mt-3 flex flex-wrap gap-2">
              {SERVICE_FORMS.map((form) => (
                <label
                  key={form}
                  className={`cursor-pointer rounded-full border px-4 py-2 text-sm font-medium transition-colors ${
                    serviceForm === form
                      ? 'border-brand bg-brand-soft text-brand-strong'
                      : 'border-border bg-surface text-muted hover:text-foreground'
                  }`}
                >
                  <input
                    type="radio"
                    name="serviceForm"
                    value={form}
                    checked={serviceForm === form}
                    onChange={() => setServiceForm(form)}
                    className="sr-only"
                  />
                  {form}
                </label>
              ))}
            </div>
          </fieldset>
        </Card>

        <Card>
          <fieldset>
            <legend className="text-sm font-semibold">주요 타깃</legend>
            <div className="mt-3 flex flex-wrap gap-2">
              {TARGETS.map((t) => (
                <label
                  key={t}
                  className={`cursor-pointer rounded-full border px-4 py-2 text-sm font-medium transition-colors ${
                    target === t
                      ? 'border-brand bg-brand-soft text-brand-strong'
                      : 'border-border bg-surface text-muted hover:text-foreground'
                  }`}
                >
                  <input
                    type="radio"
                    name="target"
                    value={t}
                    checked={target === t}
                    onChange={() => setTarget(t)}
                    className="sr-only"
                  />
                  {t}
                </label>
              ))}
            </div>
          </fieldset>
        </Card>

        <Card>
          <fieldset>
            <legend className="text-sm font-semibold">보유 리소스</legend>
            <p className="kr-text mt-1 text-xs text-muted">
              리소스가 적을수록 제안하는 기능 범위를 좁혀 보여줍니다.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {RESOURCES.map((r) => (
                <label
                  key={r}
                  className={`cursor-pointer rounded-full border px-4 py-2 text-sm font-medium transition-colors ${
                    resource === r
                      ? 'border-brand bg-brand-soft text-brand-strong'
                      : 'border-border bg-surface text-muted hover:text-foreground'
                  }`}
                >
                  <input
                    type="radio"
                    name="resource"
                    value={r}
                    checked={resource === r}
                    onChange={() => setResource(r)}
                    className="sr-only"
                  />
                  {r}
                </label>
              ))}
            </div>
          </fieldset>
        </Card>

        <Card>
          <label htmlFor="extra" className="text-sm font-semibold">
            추가 조건 <span className="font-normal text-muted">(선택)</span>
          </label>
          <textarea
            id="extra"
            value={extra}
            maxLength={EXTRA_MAX_LENGTH}
            onChange={(e) => setExtra(e.target.value)}
            rows={4}
            placeholder="예: 초기 사용자는 이미 확보되어 있고, 결제 기능은 나중에 붙이고 싶어요."
            className="kr-text mt-3 w-full rounded-xl border border-border bg-surface px-3 py-2.5 text-sm"
          />
          <p className="mt-1 text-right text-xs text-muted tabular-nums">
            {extra.length} / {EXTRA_MAX_LENGTH}자
          </p>
        </Card>

        <div className="flex justify-end">
          <Button type="submit" disabled={!problemId}>
            맞춤 아이디어 받기
          </Button>
        </div>
      </form>
    </div>
  );
}
