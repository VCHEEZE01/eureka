'use client';

/**
 * 문제 상세 / 근거 확인 (PRD F04) — 근거 페이지.
 *
 * 판단 흐름: "진짜야?"(⑧) → "꾸준해?"(④) → "얼마나 아파?"(⑦) → "돈 돼?"(①)
 *           → "누구 거야?"(⑤) → "이미 있어?"(②) → 근거 목록(⑨) → AI 서술(⑥⑩)
 * 신뢰가 먼저 서지 않으면 나머지 숫자는 읽히지 않는다는 순서다.
 *
 * ★ 아이디어 보기 / 개인화하기는 현재 잠금 기능이다. 버튼은 지우지 않고
 *   비활성 카드로 바꾼다.
 */

import { AlertCircle, ArrowRight, ChevronLeft, SlidersHorizontal } from 'lucide-react';
import { useState, type ReactNode } from 'react';
import { AppShell, Page } from '@/components/AppShell';
import { SaveButton } from '@/components/SaveButton';
import {
  AiPanel,
  Badge,
  Body,
  Caption,
  Card,
  CardTitle,
  Chip,
  Divider,
  EmptyState,
  EvidencePanel,
  PageTitle,
  buttonClass,
} from '@/components/ui';
import { CountWithDenominator } from '@/components/evidence/CountWithDenominator';
import { GateChecklist } from '@/components/evidence/GateChecklist';
import { JudgedBadge } from '@/components/evidence/JudgedBadge';
import { StackedBar, StatBar, TimelineBar } from '@/components/evidence/StatBar';
import type { Problem } from '@/api/types';
import { DATA_MODE } from '@/api/client';
import { useProblem, useProblems } from '@/hooks/useProblems';
import { NavLink } from '@/lib/nav';
import { useStore } from '@/lib/store';
import { countMatchesFor, matchTarget } from '@/lib/targetMatch';
import { MIN_LABELED_TO_SHOW, sourceCount, type TargetProfile } from '@/lib/types';

export function ProblemDetailScreen({ problemId }: { problemId: string }) {
  const { problem, loading, error } = useProblem(problemId);
  const { problems } = useProblems();
  const { target } = useStore();
  const [evidenceFilter, setEvidenceFilter] = useState<EvidenceFilter>('all');

  if (!problem) {
    return (
      <AppShell>
        <Page>
          <EmptyState
            title={loading ? '문제를 불러오는 중입니다' : '문제를 표시할 수 없습니다'}
            description={error || (loading ? '저장된 근거를 확인하고 있습니다.' : '주소가 잘못되었거나 게시되지 않은 문제일 수 있습니다.')}
            action={
              <NavLink to="/problems" className={buttonClass('primary')}>
                문제 목록으로
              </NavLink>
            }
          />
        </Page>
      </AppShell>
    );
  }

  const { signals, gate } = problem;
  // ★ api/types.ts엔 relatedIds가 없다(계약에서 제거됨) — 같은 카테고리의 다른 문제로 대체한다.
  const related = problems.filter((p) => p.id !== problem.id && p.category === problem.category).slice(0, 2);

  const dateTotal = signals.weekly_counts.reduce((sum, w) => sum + w.count, 0) + signals.undated_count;
  const maxWeekly = Math.max(1, ...signals.weekly_counts.map((w) => w.count));
  const maxSourceKind = Math.max(1, ...Object.values(signals.source_kind_counts));

  const strongPain = signals.severity_counts['높음'] ?? 0;
  const filteredEvidence = problem.evidence.filter((e) => {
    if (evidenceFilter === 'strong') return e.severity === '높음';
    if (evidenceFilter === 'payment') return Boolean(e.has_payment_signal);
    if (evidenceFilter === 'need') return Boolean(e.has_need_signal);
    return true;
  });

  return (
    <AppShell>
      <Page>
        <Caption>{DATA_MODE === 'demo' ? '디자인 데모 · 예시 데이터' : '실제 수집 데이터 · 게시 기준 통과'}</Caption>
        {/* ① 헤더 */}
        <div>
          <NavLink
            to="/problems"
            className="inline-flex items-center gap-1 text-[14px] text-text-secondary hover:text-text-primary mb-6"
          >
            <ChevronLeft size={16} aria-hidden />
            문제 탐색
          </NavLink>

          <div className="flex flex-col gap-5 prose-width">
            <Badge tone="blue">{problem.category}</Badge>
            <PageTitle>{problem.title}</PageTitle>
            <Body className="text-[17px]">{problem.one_liner}</Body>

            <div className="flex flex-wrap items-center gap-6 pt-1">
              <Metric label="관련 사례" value={`${problem.case_count}건`} />
              <Metric label="출처" value={`${sourceCount(problem)}곳`} />
              <Metric label="관측 기간" value={`${signals.observed_weeks}주에 걸쳐 관측`} />
            </div>
          </div>
        </div>

        {/* ② 근거 요약 스트립 */}
        <div className="flex flex-wrap gap-2">
          <SummaryPill href="#trust" label={`출처 ${sourceCount(problem)}곳`} />
          <SummaryPill href="#consistency" label={`${signals.observed_weeks}주 관측`} />
          <SummaryPill
            href="#pain"
            label={signals.severity_labeled_count >= MIN_LABELED_TO_SHOW ? `강한 불만 ${strongPain}건` : '불편 강도 표본 부족'}
          />
          <SummaryPill href="#money" label={`돈 언급 ${signals.payment_signal_count}건`} />
          <SummaryPill href="#services" label={`언급된 서비스 ${signals.mentioned_services.length}개`} />
        </div>

        {/* ━━━ 실제 수집된 근거 (Blue) ━━━ */}
        <EvidencePanel title="이 문제, 믿어도 될까요">
          <div className="flex flex-col gap-10">
            {/* ⑧ 신뢰 */}
            <div id="trust" className="flex flex-col gap-4">
              <h4 className="text-[18px] font-semibold kr">이 문제를 믿어도 되는가</h4>
              <GateChecklist
                gate={gate}
                caseCount={problem.case_count}
                sourceCount={sourceCount(problem)}
                evidenceCount={problem.evidence.length}
              />
              <div>
                <p className="text-[13px] font-semibold text-blue mb-2">출처 유형별 분포</p>
                <StatBar
                  items={Object.entries(signals.source_kind_counts).map(([label, value]) => ({
                    label,
                    value,
                    total: maxSourceKind,
                  }))}
                />
              </div>
              <div>
                <p className="text-[13px] font-semibold text-blue mb-2">매체별 분포</p>
                <StatBar
                  items={Object.entries(signals.source_name_counts).map(([label, value]) => ({
                    label,
                    value,
                    total: Math.max(1, ...Object.values(signals.source_name_counts)),
                  }))}
                />
              </div>
              <div>
                <p className="text-[13px] font-semibold text-blue mb-2">관측 기간</p>
                <TimelineBar first={signals.first_posted_at} last={signals.last_posted_at} />
              </div>
            </div>

            <Divider />

            {/* ④ 꾸준함 */}
            <div id="consistency" className="flex flex-col gap-4">
              <h4 className="text-[18px] font-semibold kr">얼마나 꾸준히 나타나나</h4>
              {signals.weekly_counts.length > 0 ? (
                <StatBar
                  orientation="vertical"
                  items={signals.weekly_counts.map((w) => ({
                    label: w.week.replace(/^\d{4}-/, ''),
                    value: w.count,
                    total: maxWeekly,
                    dim: w.partial,
                  }))}
                />
              ) : (
                <Caption>주별 분포를 계산할 근거가 아직 부족합니다.</Caption>
              )}
              <Caption>
                주 1회 배치로 검색 API를 최신순 조회합니다. 이 분포는 언급량 증감이 아니라 수집
                창 안에서 발견된 글의 작성일 분포입니다.
              </Caption>
              {signals.undated_count > 0 ? (
                <Caption>
                  근거 {dateTotal}건 중 {signals.undated_count}건은 작성일이 없어 빠져 있습니다.
                </Caption>
              ) : null}
            </div>

            <Divider />

            {/* ⑦ 불편 강도 */}
            <div id="pain" className="flex flex-col gap-4">
              <h4 className="text-[18px] font-semibold kr flex items-center gap-2">
                얼마나 불편해하나 <JudgedBadge />
              </h4>
              {signals.severity_labeled_count >= MIN_LABELED_TO_SHOW ? (
                <>
                  <StackedBar
                    segments={[
                      { key: 'high', label: '높음', value: signals.severity_counts['높음'] ?? 0, className: 'bg-blue-hover' },
                      { key: 'mid', label: '중간', value: signals.severity_counts['중간'] ?? 0, className: 'bg-blue' },
                      { key: 'low', label: '낮음', value: signals.severity_counts['낮음'] ?? 0, className: 'bg-blue-light' },
                    ]}
                  />
                  <CountWithDenominator value={strongPain} total={signals.severity_labeled_count} />
                </>
              ) : (
                <Caption>불편 강도가 드러난 근거가 부족합니다.</Caption>
              )}
              <p className="text-[15px] kr">해결책을 원한 언급 {signals.need_signal_count}건</p>
            </div>

            <Divider />

            {/* ① 돈 */}
            <div id="money" className="flex flex-col gap-4">
              <h4 className="text-[18px] font-semibold kr">돈이 걸린 문제인가</h4>
              <StatBar items={[{ label: '돈 관련 언급', value: signals.payment_signal_count, total: problem.case_count }]} />
              <CountWithDenominator
                value={signals.payment_signal_count}
                total={problem.case_count}
                totalLabel="전체"
              />
            </div>

            <Divider />

            {/* ⑤ 누가 */}
            <div id="who" className="flex flex-col gap-5">
              <h4 className="text-[18px] font-semibold kr">누가 겪고 있나</h4>
              <div>
                <p className="text-[13px] font-semibold text-text-muted mb-2">어디서 말하고 있나</p>
                <StatBar
                  items={Object.entries(signals.source_kind_counts).map(([label, value]) => ({
                    label,
                    value,
                    total: maxSourceKind,
                  }))}
                />
              </div>

              <div className="flex flex-col gap-3">
                <p className="text-[13px] font-semibold text-text-muted flex items-center gap-2">
                  드러난 속성 <JudgedBadge />
                </p>
                <AttributeRow title="역할" counts={signals.role_counts} labeled={signals.role_labeled_count} />
                <AttributeRow title="연령" counts={signals.age_counts} labeled={signals.age_labeled_count} />
                <AttributeRow title="성별" counts={signals.gender_counts} labeled={signals.gender_labeled_count} />
              </div>

              <Divider />

              <div className="flex flex-col gap-2">
                <p className="text-[13px] font-semibold text-blue">당신의 타겟과 대조</p>
                {target ? (
                  <TargetContrast problem={problem} target={target} />
                ) : (
                  <Caption>
                    타겟을 설정하면 이 문제가 실제 근거와 얼마나 관련 있는지 보여드립니다.{' '}
                    <NavLink to="/onboarding" className="text-blue font-semibold">
                      타겟 설정하기
                    </NavLink>
                  </Caption>
                )}
              </div>
            </div>

            <Divider />

            {/* ② 유사 서비스 */}
            <div id="services" className="flex flex-col gap-3">
              <h4 className="text-[18px] font-semibold kr">이미 나와 있는 것들</h4>
              {signals.mentioned_services.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {signals.mentioned_services.map((s) => (
                    <Badge key={s.name}>
                      {s.name} {s.count}건
                    </Badge>
                  ))}
                </div>
              ) : (
                <Caption>원문에서 함께 언급된 서비스가 아직 발견되지 않았습니다.</Caption>
              )}
              <Caption>원문에 직접 언급된 이름만 셉니다. 앱 리뷰는 아직 수집하지 않습니다.</Caption>
            </div>

            <Divider />

            {/* ⑨ 근거 목록 */}
            <div className="flex flex-col gap-4">
              <h4 className="text-[18px] font-semibold kr">실제 사용자 불편 {problem.evidence.length}건</h4>
              <div className="flex flex-wrap gap-2" aria-label="근거 필터">
                {EVIDENCE_FILTERS.map((filter) => (
                  <Chip
                    key={filter.value}
                    selected={evidenceFilter === filter.value}
                    onClick={() => setEvidenceFilter(filter.value)}
                  >
                    {filter.label}
                  </Chip>
                ))}
              </div>
              {filteredEvidence.length > 0 ? (
                <ul className="flex flex-col gap-5" aria-live="polite">
                  {filteredEvidence.map((e) => (
                    <li key={e.raw_item_id} className="flex flex-col gap-2">
                      <p className="text-[16px] leading-[1.6] kr">{e.summary}</p>
                      <Caption>{e.source_name || '출처 미기록'} · {e.posted_at ? e.posted_at.slice(0, 10) : '작성일 미기록'}</Caption>
                      {e.source_url && /^https?:\/\//i.test(e.source_url) ? <a href={e.source_url} target="_blank" rel="noopener noreferrer" className="text-blue underline">원문 확인하기</a> : <Caption>원문 링크 미기록</Caption>}
                      {e.excerpt ? (
                        <p className="text-[15px] text-text-secondary kr border-l-2 border-blue pl-3 italic">
                          “{e.excerpt}”
                        </p>
                      ) : null}
                    </li>
                  ))}
                </ul>
              ) : (
                <Caption>이 조건에 해당하는 근거가 없습니다.</Caption>
              )}
            </div>
          </div>
        </EvidencePanel>

        {/* ━━━ AI가 생성한 설명 (회색) ━━━ */}
        <AiPanel title="이 문제를 이렇게 읽었습니다">
          <div className="flex flex-col gap-4 prose-width">
            <Body>{problem.description}</Body>
            <div>
              <p className="text-[15px] font-semibold mb-1.5">왜 이런 문제가 생겼나</p>
              <Body>{problem.context}</Body>
            </div>
            <div>
              <p className="text-[15px] font-semibold mb-1.5">만들기에 얼마나 복잡한가</p>
              <Body>{problem.complexity_note}</Body>
            </div>
          </div>
        </AiPanel>

        {/* 비슷한 문제 */}
        {related.length > 0 ? (
          <section className="flex flex-col gap-5">
            <CardTitle>비슷한 문제</CardTitle>
            <ul className="grid gap-5 md:grid-cols-2">
              {related.map((p) => (
                <li key={p.id}>
                  <NavLink to={`/problems/${p.id}`}>
                    <Card interactive className="h-full flex flex-col gap-2">
                      <Caption>{p.category}</Caption>
                      <p className="text-[17px] font-semibold kr">{p.title}</p>
                      <Body>{p.one_liner}</Body>
                    </Card>
                  </NavLink>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {/* 아이디어 CTA — 현재 잠금 기능. 버튼은 지우지 않고 비활성 카드로 바꾼다. */}
        <Card className="flex flex-col gap-3 max-w-[640px]">
          <p className="text-[16px] font-semibold kr">아이디어 기능은 준비 중입니다</p>
          <Body>이 문제를 아이디어로 연결하거나 내 조건에 맞게 개인화하는 기능은 곧 열립니다.</Body>
          <div className="flex flex-wrap gap-3 pt-1">
            <button type="button" disabled className={buttonClass('primary')}>
              아이디어 보기
              <ArrowRight size={18} aria-hidden />
            </button>
            <button type="button" disabled className={buttonClass('secondary')}>
              <SlidersHorizontal size={18} aria-hidden />
              내 조건에 맞게 개인화하기
            </button>
            <SaveButton
              kind="problem"
              refId={problem.id}
              title={problem.title}
              subtitle={problem.one_liner}
              path={`/problems/${problem.id}`}
            />
          </div>
        </Card>
      </Page>
    </AppShell>
  );
}

type EvidenceFilter = 'all' | 'strong' | 'payment' | 'need';

const EVIDENCE_FILTERS: { value: EvidenceFilter; label: string }[] = [
  { value: 'all', label: '전체' },
  { value: 'strong', label: '강한 불만' },
  { value: 'payment', label: '돈 언급' },
  { value: 'need', label: '해결책 탐색' },
];

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[13px] text-text-muted mb-0.5">{label}</p>
      <p className="text-[18px] font-semibold">{value}</p>
    </div>
  );
}

function SummaryPill({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      className="inline-flex items-center h-8 px-3 rounded-lg bg-blue-light text-blue text-[13px] font-medium hover:bg-blue hover:text-white transition-colors"
    >
      {label}
    </a>
  );
}

function AttributeRow({
  title,
  counts,
  labeled,
}: {
  title: string;
  counts: Record<string, number>;
  labeled: number;
}): ReactNode {
  if (labeled < MIN_LABELED_TO_SHOW) {
    return (
      <p className="text-[14px] text-text-muted kr flex items-center gap-1.5">
        <AlertCircle size={14} aria-hidden />
        {title}이 드러난 근거가 부족합니다 ({labeled}건)
      </p>
    );
  }
  return (
    <div className="flex flex-col gap-1.5">
      <Caption>
        {title}이 드러난 {labeled}건 중
      </Caption>
      <div className="flex flex-wrap gap-2">
        {Object.entries(counts).map(([k, v]) => (
          <Badge key={k}>
            {k} {v}
          </Badge>
        ))}
      </div>
    </div>
  );
}

function TargetContrast({ problem, target }: { problem: Problem; target: TargetProfile }) {
  const result = matchTarget(problem, target);
  const jobPlaceKeywords = [...target.jobs, ...target.places].filter((k) => k.trim().length >= 2);
  const ageGenderLabel = [target.age, target.gender].filter(Boolean).join(' · ');

  if (result.totalEvidence === 0 || (jobPlaceKeywords.length === 0 && !ageGenderLabel)) {
    return <Caption>대조할 근거가 부족합니다.</Caption>;
  }

  const rows: { label: string; count: number }[] = jobPlaceKeywords.map((kw) => ({
    label: `'${kw}'`,
    count: countMatchesFor(problem, [kw]),
  }));
  if (ageGenderLabel) {
    rows.push({ label: ageGenderLabel, count: countMatchesFor(problem, [target.age, target.gender]) });
  }

  return (
    <ul className="flex flex-col gap-1.5">
      {rows.map((r) => (
        <li key={r.label} className="text-[14px] kr">
          <b className="text-text-primary">{r.label}</b>{' '}
          {r.count > 0 ? (
            <CountWithDenominator value={r.count} total={result.totalEvidence} totalLabel="근거" />
          ) : (
            <span className="text-text-muted">대조할 근거가 부족합니다</span>
          )}
        </li>
      ))}
    </ul>
  );
}
