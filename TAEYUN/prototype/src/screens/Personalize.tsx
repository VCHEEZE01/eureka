'use client';

/**
 * 6. 개인화 설정 / 7. 개인화 결과 목록 / 8. 개인화 결과 상세
 * (PRD F07, F08) — ★개인화 포인트 3
 *
 * PRD 10절 TBD 반영: "기술 난이도" 슬라이더는 입력받지 않는다.
 * 리소스를 바탕으로 시스템이 난이도 참고값을 추론해 결과에 표시한다.
 * 로그인이 필요한 기능이다.
 */

import { ChevronLeft, Lock, SlidersHorizontal } from 'lucide-react';
import { useState } from 'react';
import { AgentProgress } from '@/components/AgentProgress';
import { AppShell, Page } from '@/components/AppShell';
import { SaveButton } from '@/components/SaveButton';
import { IdeaBody } from './Ideas';
import {
  Badge,
  Body,
  Button,
  Caption,
  Card,
  CardTitle,
  EmptyState,
  Field,
  PageTitle,
  TextArea,
  buttonClass,
} from '@/components/ui';
import { getProblem } from '@/data/problems';
import { NavLink, useNav } from '@/lib/nav';
import { personalize, runId } from '@/lib/personalize';
import { useStore } from '@/lib/store';
import {
  EXTRA_MAX,
  RESOURCES,
  SERVICE_FORMS,
  TARGETS,
  type PersonalizeInput,
  type Resource,
  type ServiceForm,
  type Target,
} from '@/lib/types';

/* ── 6. 개인화 설정 ────────────────────────────────────────────── */

export function PersonalizeFormScreen({ baseId }: { baseId: string }) {
  const { user, combined, addRun } = useStore();
  const { go } = useNav();

  // baseId는 일반 문제(p*) 또는 조합된 문제정의(c*) 둘 다 될 수 있다.
  const problem = getProblem(baseId);
  const combo = combined.find((c) => c.id === baseId);
  const baseTitle = problem?.title ?? combo?.title;

  const [serviceForm, setServiceForm] = useState<ServiceForm>('웹 서비스');
  const [target, setTarget] = useState<Target>('B2C');
  const [resource, setResource] = useState<Resource>('1인');
  const [extra, setExtra] = useState('');
  const [generating, setGenerating] = useState(false);

  if (!baseTitle) {
    return (
      <AppShell>
        <Page>
          <EmptyState
            title="기준이 될 문제를 찾을 수 없습니다"
            description="문제 상세나 조합된 문제정의에서 개인화를 시작해 주세요."
            action={
              <NavLink to="/problems" className={buttonClass('primary')}>
                문제 탐색으로
              </NavLink>
            }
          />
        </Page>
      </AppShell>
    );
  }

  // PRD F07: 로그인 필요
  if (!user) {
    return (
      <AppShell>
        <Page>
          <div className="max-w-[560px] flex flex-col gap-6">
            <span className="inline-flex w-11 h-11 items-center justify-center rounded-[12px] bg-blue-light text-blue">
              <Lock size={20} aria-hidden />
            </span>
            <PageTitle>개인화는 로그인이 필요합니다</PageTitle>
            <Body>
              조건에 맞춰 만든 아이디어를 나중에 다시 보려면 계정이 필요합니다. 문제 탐색과 기본
              아이디어는 로그인 없이 계속 보실 수 있습니다.
            </Body>
            <div className="flex flex-wrap gap-3">
              <NavLink to="/login" className={buttonClass('primary')}>
                로그인하고 계속하기
              </NavLink>
              <NavLink to="/problems" className={buttonClass('ghost')}>
                문제 탐색으로 돌아가기
              </NavLink>
            </div>
          </div>
        </Page>
      </AppShell>
    );
  }

  const input: PersonalizeInput = { problemId: baseId, serviceForm, target, resource, extra };

  const finish = () => {
    const ideas = personalize(input, combo);
    const run = {
      id: runId(input),
      createdAt: new Date().toISOString(),
      input,
      combined: combo,
      ideas,
    };
    addRun(run);
    go(`/personalize/${run.id}`);
  };

  const backTo = combo ? `/combined/${combo.id}` : `/problems/${baseId}`;

  return (
    <AppShell>
      <Page>
        <div>
          <NavLink
            to={backTo}
            className="inline-flex items-center gap-1 text-[14px] text-text-secondary hover:text-text-primary mb-6"
          >
            <ChevronLeft size={16} aria-hidden />
            돌아가기
          </NavLink>
          <div className="prose-width flex flex-col gap-4">
            <Caption>기준 문제</Caption>
            <PageTitle>{baseTitle}</PageTitle>
            <Body>
              아래 조건을 넣으면 이 문제에서 나온 아이디어를 조건에 맞게 좁혀드립니다.
            </Body>
          </div>
        </div>

        {generating ? (
          <AgentProgress label="조건에 맞는 아이디어를 만들고 있습니다" onDone={finish} />
        ) : (
          <div className="flex flex-col gap-10 max-w-[760px]">
            <OptionGroup
              label="어떤 형태로 만들 건가요"
              options={SERVICE_FORMS}
              value={serviceForm}
              onChange={setServiceForm}
            />
            <OptionGroup
              label="누구를 위한 서비스인가요"
              options={TARGETS}
              value={target}
              onChange={setTarget}
            />
            <OptionGroup
              label="쓸 수 있는 리소스는요"
              options={RESOURCES}
              value={resource}
              onChange={setResource}
              hint="리소스가 적을수록 기능 범위를 줄여 제안합니다. 기술 난이도는 따로 묻지 않고 시스템이 추론합니다."
            />

            <Field
              label="추가로 알려주실 조건이 있나요"
              hint={`선택 사항입니다. ${EXTRA_MAX}자까지 쓸 수 있습니다.`}
              htmlFor="extra"
            >
              <TextArea
                id="extra"
                value={extra}
                onChange={setExtra}
                maxLength={EXTRA_MAX}
                placeholder="예: 이미 만들어둔 로그인 기능을 재활용하고 싶어요"
              />
              <Caption>
                {extra.length} / {EXTRA_MAX}
              </Caption>
            </Field>

            <div className="flex flex-wrap items-center gap-3">
              <Button onClick={() => setGenerating(true)}>
                <SlidersHorizontal size={18} aria-hidden />
                아이디어 만들기
              </Button>
              <Caption>같은 조건이면 항상 같은 결과가 나옵니다.</Caption>
            </div>
          </div>
        )}
      </Page>
    </AppShell>
  );
}

function OptionGroup<T extends string>({
  label,
  hint,
  options,
  value,
  onChange,
}: {
  label: string;
  hint?: string;
  options: readonly T[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <Field label={label} hint={hint}>
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => (
          <button
            key={opt}
            type="button"
            onClick={() => onChange(opt)}
            aria-pressed={value === opt}
            className={`h-12 px-5 rounded-[12px] text-[15px] font-medium border transition-colors ${
              value === opt
                ? 'bg-blue-light border-blue text-blue'
                : 'bg-bg border-control-border text-control-text hover:bg-bg-subtle'
            }`}
          >
            {opt}
          </button>
        ))}
      </div>
    </Field>
  );
}

/* ── 7. 개인화 결과 목록 ───────────────────────────────────────── */

export function PersonalizeResultScreen({ id }: { id: string }) {
  const { runs } = useStore();
  const run = runs.find((r) => r.id === id);

  if (!run) {
    return (
      <AppShell>
        <Page>
          <EmptyState
            title="개인화 결과를 찾을 수 없습니다"
            description="결과는 이 브라우저에 보관됩니다. 저장 기록이 지워졌거나 다른 기기에서 만든 것일 수 있습니다."
            action={
              <NavLink to="/problems" className={buttonClass('primary')}>
                문제 탐색으로
              </NavLink>
            }
          />
        </Page>
      </AppShell>
    );
  }

  const baseTitle = run.combined?.title ?? getProblem(run.input.problemId)?.title ?? '기준 문제';

  return (
    <AppShell>
      <Page>
        <div className="prose-width flex flex-col gap-4">
          <Caption>{baseTitle}</Caption>
          <PageTitle>조건에 맞춘 아이디어 {run.ideas.length}개</PageTitle>
          <div className="flex flex-wrap gap-2">
            <Badge tone="blue">{run.input.serviceForm}</Badge>
            <Badge>{run.input.target}</Badge>
            <Badge>{run.input.resource}</Badge>
          </div>
          {run.input.extra?.trim() ? (
            <Body className="border-l-2 border-border pl-3">
              추가 조건: {run.input.extra}
            </Body>
          ) : null}
        </div>

        <div className="flex flex-wrap gap-3">
          <NavLink
            to={`/personalize/from/${run.input.problemId}`}
            className={buttonClass('secondary')}
          >
            조건 다시 설정
          </NavLink>
        </div>

        <ul className="flex flex-col gap-5">
          {run.ideas.map((idea) => (
            <li key={idea.id}>
              <Card interactive className="flex flex-col gap-4">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <NavLink
                    to={`/personalize/${run.id}/${idea.id}`}
                    className="flex-1 min-w-0 flex flex-col gap-2"
                  >
                    <CardTitle>{idea.name}</CardTitle>
                    <Body>{idea.oneLiner}</Body>
                  </NavLink>
                  <div className="text-right shrink-0">
                    <p className="text-[13px] text-text-muted mb-0.5">조건 일치도</p>
                    <p className="text-[22px] font-bold text-blue">{idea.matchScore}</p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Badge tone="blue">{idea.serviceForm}</Badge>
                  <Badge>{idea.target}</Badge>
                  <Badge>기술 난이도 {idea.difficulty}</Badge>
                </div>

                <p className="text-[15px] text-text-secondary kr border-l-2 border-blue pl-3">
                  {idea.fitReason}
                </p>

                <div className="flex flex-wrap gap-3 pt-1">
                  <NavLink
                    to={`/personalize/${run.id}/${idea.id}`}
                    className="text-[14px] font-semibold text-blue"
                  >
                    자세히 보기 →
                  </NavLink>
                </div>
              </Card>
            </li>
          ))}
        </ul>

        <p className="text-[13px] text-text-muted kr">
          조건 일치도는 입력하신 조건과 아이디어 속성이 얼마나 맞는지를 나타낸 값입니다. 시장성이나
          성공 가능성과는 관련이 없습니다.
        </p>
      </Page>
    </AppShell>
  );
}

/* ── 8. 개인화 결과 상세 ───────────────────────────────────────── */

export function PersonalizedIdeaDetailScreen({ id, ideaId }: { id: string; ideaId: string }) {
  const { runs } = useStore();
  const run = runs.find((r) => r.id === id);
  const idea = run?.ideas.find((i) => i.id === ideaId);

  if (!run || !idea) {
    return (
      <AppShell>
        <Page>
          <EmptyState
            title="아이디어를 찾을 수 없습니다"
            description="결과는 이 브라우저에 보관됩니다. 저장 기록이 지워졌을 수 있습니다."
            action={
              <NavLink to="/problems" className={buttonClass('primary')}>
                문제 탐색으로
              </NavLink>
            }
          />
        </Page>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <Page>
        <div>
          <NavLink
            to={`/personalize/${run.id}`}
            className="inline-flex items-center gap-1 text-[14px] text-text-secondary hover:text-text-primary mb-6"
          >
            <ChevronLeft size={16} aria-hidden />
            결과 목록
          </NavLink>

          <div className="prose-width flex flex-col gap-5">
            <PageTitle>{idea.name}</PageTitle>
            <Body className="text-[17px]">{idea.oneLiner}</Body>
            <div className="flex flex-wrap gap-2">
              <Badge tone="blue">{idea.serviceForm}</Badge>
              <Badge>{idea.target}</Badge>
              <Badge>기술 난이도 {idea.difficulty}</Badge>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <SaveButton
            kind="personalized"
            refId={idea.id}
            title={idea.name}
            subtitle={idea.oneLiner}
            path={`/personalize/${run.id}/${idea.id}`}
          />
        </div>

        {/* 개인화에만 있는 영역 — 왜 내 조건에 맞는가 */}
        <section className="rounded-[16px] border border-blue-light bg-blue-soft p-6 prose-width">
          <p className="text-[13px] font-semibold text-blue mb-3">내 조건에 맞춘 부분</p>
          <div className="flex flex-col gap-4">
            <div>
              <p className="text-[15px] font-semibold mb-1.5">조건 적합 이유</p>
              <Body className="text-text-primary">{idea.fitReason}</Body>
            </div>
            <div>
              <p className="text-[15px] font-semibold mb-1.5">권장 범위</p>
              <Body className="text-text-primary">{idea.scopeNote}</Body>
            </div>
          </div>
        </section>

        <IdeaBody idea={idea} />
      </Page>
    </AppShell>
  );
}
