'use client';

/**
 * F05 초개인화 — 요청 폼.
 * `?problem=<id>`로 기준 문제를 자동 적용한다. 개인화는 로그인이 필요하므로
 * 비로그인 상태에서는 폼 대신 로그인 안내를 보여준다.
 */

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useMemo, useState, type FormEvent, type ReactNode } from 'react';
import { ArrowRightIcon, SparkIcon } from '@/components/icons';
import {
  Button,
  ButtonLink,
  Card,
  FIELD_CLASS,
  PageHeader,
  Skeleton,
} from '@/components/ui';
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
      <PageHeader title="초개인화" description="조건을 불러오는 중입니다…" />
      <Skeleton className="h-32" />
      <Skeleton className="h-64" />
    </div>
  );
}

const HEADER = {
  title: '초개인화',
  description:
    '만들고 싶은 형태·타깃·리소스를 알려주면 그 조건에 맞게 아이디어를 다시 구성합니다.',
};

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
        <PageHeader
          eyebrow={<SparkIcon className="size-4 text-ai" />}
          title={HEADER.title}
          description="내 조건에 맞게 아이디어를 좁혀 봅니다."
        />
        <Card className="aurora border-dashed py-12 text-center">
          <p className="kr-text text-lg font-bold">개인화는 로그인이 필요합니다</p>
          <p className="kr-text mx-auto mt-2 max-w-md text-sm text-muted">
            만들고 싶은 형태·타깃·리소스를 반영한 맞춤 아이디어와 저장 기능은 로그인한
            사용자만 이용할 수 있습니다.
          </p>
          <div className="mt-6 flex justify-center">
            <ButtonLink href={`/login?next=${encodeURIComponent(nextPath)}`}>
              로그인하고 계속하기
              <ArrowRightIcon />
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
    <div className="space-y-8 pb-28 sm:pb-8">
      <PageHeader
        eyebrow={
          <span className="display text-sm tracking-[0.18em] text-ai uppercase">
            Personalize
          </span>
        }
        title={HEADER.title}
        description={HEADER.description}
      />

      <form onSubmit={handleSubmit} className="space-y-5">
        <Card>
          <fieldset>
            <legend className="text-sm font-bold">기준 문제</legend>
            {queryProblem ? (
              <div className="kr-text mt-3 rounded-xl border border-border bg-surface-muted px-4 py-3.5 text-sm">
                <p className="font-semibold">{queryProblem.title}</p>
                <p className="mt-1 text-muted">{queryProblem.oneLiner}</p>
                <p className="mt-2.5 text-xs text-muted">
                  이 문제를 기준으로 자동 적용됩니다.{' '}
                  <Link
                    href={`/problems/${queryProblem.id}`}
                    className="focus-ring rounded font-medium text-brand underline underline-offset-2"
                  >
                    문제 상세 보기
                  </Link>
                </p>
              </div>
            ) : (
              <div className="mt-3 space-y-2">
                {problemParam && (
                  <p className="kr-text text-sm text-brand-strong">
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
                  className={FIELD_CLASS}
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

        {/* 세 개의 선택지를 카드 하나로 합쳤다. 이전에는 카드 세 장으로 나뉘어
            폼 전체가 한 화면을 넘겼고 제출 버튼이 스크롤 밖에 있었다. */}
        <Card className="divide-y divide-border p-0">
          <ChipGroup
            legend="만들고 싶은 형태"
            name="serviceForm"
            options={SERVICE_FORMS}
            value={serviceForm}
            onChange={setServiceForm}
          />
          <ChipGroup
            legend="주요 타깃"
            name="target"
            options={TARGETS}
            value={target}
            onChange={setTarget}
          />
          <ChipGroup
            legend="보유 리소스"
            hint="리소스가 적을수록 제안하는 기능 범위를 좁혀 보여줍니다."
            name="resource"
            options={RESOURCES}
            value={resource}
            onChange={setResource}
          />
        </Card>

        <Card>
          <label htmlFor="extra" className="text-sm font-bold">
            추가 조건 <span className="font-normal text-muted">(선택)</span>
          </label>
          <textarea
            id="extra"
            value={extra}
            maxLength={EXTRA_MAX_LENGTH}
            onChange={(e) => setExtra(e.target.value)}
            rows={4}
            placeholder="예: 초기 사용자는 이미 확보되어 있고, 결제 기능은 나중에 붙이고 싶어요."
            className={`kr-text mt-3 resize-y ${FIELD_CLASS}`}
          />
          <p className="mt-1.5 text-right text-xs text-muted tabular-nums">
            {extra.length} / {EXTRA_MAX_LENGTH}자
          </p>
        </Card>

        {/*
          모바일에서는 화면 아래 고정, 데스크톱에서는 폼 끝에 붙는 제출 바.
          선택한 조건을 함께 보여줘서 스크롤을 올리지 않아도 확인할 수 있게 한다.
        */}
        <div className="fixed inset-x-0 bottom-0 z-30 border-t border-border bg-background/95 px-4 py-3 backdrop-blur sm:static sm:rounded-2xl sm:border sm:px-5 sm:py-4">
          <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3">
            <p className="kr-text min-w-0 text-xs text-muted">
              <span className="font-semibold text-foreground">{serviceForm}</span> ·{' '}
              {target} · {resource}
              {extra.trim() && ' · 추가 조건 반영'}
            </p>
            <Button type="submit" disabled={!problemId}>
              맞춤 아이디어 받기
              <ArrowRightIcon />
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}

/**
 * 라디오 그룹을 칩 모양으로 보여준다.
 * 형태·타깃·리소스가 같은 마크업을 세 번 반복하고 있어 하나로 묶었다.
 */
function ChipGroup<T extends string>({
  legend,
  hint,
  name,
  options,
  value,
  onChange,
}: {
  legend: string;
  hint?: ReactNode;
  name: string;
  options: readonly T[];
  value: T;
  onChange: (next: T) => void;
}) {
  return (
    <fieldset className="p-5">
      <legend className="text-sm font-bold">{legend}</legend>
      {hint && <p className="kr-text mt-1 text-xs text-muted">{hint}</p>}
      <div className="mt-3 flex flex-wrap gap-2">
        {options.map((option) => {
          const active = value === option;
          return (
            <label
              key={option}
              className={`kr-text cursor-pointer rounded-full border px-4 py-2 text-sm font-medium transition-colors has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-brand ${
                active
                  ? 'border-brand bg-brand-soft text-brand-strong'
                  : 'border-border bg-surface text-muted hover:border-border-strong hover:text-foreground'
              }`}
            >
              <input
                type="radio"
                name={name}
                value={option}
                checked={active}
                onChange={() => onChange(option)}
                className="sr-only"
              />
              {option}
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
