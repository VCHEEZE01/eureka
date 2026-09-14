'use client';

/**
 * 타겟 설정 (온보딩 교체, 2026-09-11).
 *
 * ★ 예전 버전(출처 선택 → 가짜 수집 대기)을 전면 교체한다.
 *   배치는 항상 전체 출처를 수집하므로 온보딩에서 고를 것이 없다
 *   (DATA_SPEC 0절) — 대신 "누구의 문제를 찾고 있는가"를 입력받아
 *   실제 근거와 대조해 보여준다 (targetMatch.ts).
 *
 * 연령·성별·직업·장소 4개 중 최소 2개를 입력해야 시작할 수 있다.
 * "건너뛰기" 버튼은 없다 — 최소 2개 강제와 정면으로 모순되기 때문이다.
 */

import { AlertCircle, ArrowRight } from 'lucide-react';
import { useEffect, useState } from 'react';
import { AppShell, Page } from '@/components/AppShell';
import { Body, Button, Caption, Field, PageTitle, Select, TokenInput } from '@/components/ui';
import { useNav } from '@/lib/nav';
import { useStore } from '@/lib/store';
import {
  AGE_BANDS,
  GENDERS,
  TARGET_MIN_FILLED,
  TARGET_TOKEN_MAX,
  filledCount,
  type AgeBand,
  type Gender,
} from '@/lib/types';

interface InvalidState {
  age: boolean;
  gender: boolean;
  jobs: boolean;
  places: boolean;
}

const NO_INVALID: InvalidState = { age: false, gender: false, jobs: false, places: false };

export function OnboardingScreen() {
  const { target, setTarget } = useStore();
  const { go } = useNav();

  const [age, setAge] = useState<AgeBand | null>(target?.age ?? null);
  const [gender, setGender] = useState<Gender | null>(target?.gender ?? null);
  const [jobs, setJobs] = useState<string[]>(target?.jobs ?? []);
  const [places, setPlaces] = useState<string[]>(target?.places ?? []);
  const [invalid, setInvalid] = useState<InvalidState>(NO_INVALID);
  const [attempted, setAttempted] = useState(false);

  const filled = filledCount({ age, gender, jobs, places });

  // 2개가 채워지면 남은 빨간 테두리도 전부 해제한다.
  useEffect(() => {
    if (filled >= TARGET_MIN_FILLED) {
      setInvalid(NO_INVALID);
      setAttempted(false);
    }
  }, [filled]);

  const submit = () => {
    if (filled < TARGET_MIN_FILLED) {
      const next: InvalidState = {
        age: !age,
        gender: !gender,
        jobs: jobs.length === 0,
        places: places.length === 0,
      };
      setInvalid(next);
      setAttempted(true);

      // 첫 미입력 필드로 focus 이동 (id 기반 — Select/TokenInput은 ref를 전달받지 않는다)
      if (next.age) document.getElementById('age')?.focus();
      else if (next.gender) document.getElementById('gender')?.focus();
      else if (next.jobs) document.getElementById('jobs')?.focus();
      else if (next.places) document.getElementById('places')?.focus();
      return;
    }

    setTarget({ age, gender, jobs, places });
    go('/problems');
  };

  return (
    <AppShell>
      <Page>
        <div className="prose-width flex flex-col gap-4">
          <Caption>1 / 1 단계</Caption>
          <PageTitle>누구의 문제를 찾고 있나요?</PageTitle>
          <Body>
            입력한 타겟이 실제 근거에 얼마나 등장하는지 함께 보여드립니다.
          </Body>
          <Caption>4개 중 최소 2개를 입력해 주세요.</Caption>
        </div>

        {attempted ? (
          <div
            role="alert"
            className="flex items-center gap-2 rounded-[12px] border border-danger bg-bg px-4 py-3 max-w-[720px]"
          >
            <AlertCircle size={18} className="text-danger shrink-0" aria-hidden />
            <p className="text-[14px] text-danger kr">
              최소 2개 항목을 입력해야 문제 탐색을 시작할 수 있습니다.
            </p>
          </div>
        ) : null}

        <div className="flex flex-col gap-6 max-w-[720px]">
          <div className="grid gap-5 sm:grid-cols-2">
            <Field
              label="나이대"
              htmlFor="age"
              error={invalid.age ? '최소 2개가 필요합니다' : undefined}
            >
              <Select
                id="age"
                value={age ?? '미선택'}
                onChange={(v) => {
                  setAge(v === '미선택' ? null : (v as AgeBand));
                  setInvalid((s) => ({ ...s, age: false }));
                }}
                options={AGE_BANDS}
                invalid={invalid.age}
                describedBy={invalid.age ? 'age-error' : undefined}
                ariaLabel="나이대"
              />
            </Field>

            <Field
              label="성별"
              htmlFor="gender"
              error={invalid.gender ? '최소 2개가 필요합니다' : undefined}
            >
              <Select
                id="gender"
                value={gender ?? '미선택'}
                onChange={(v) => {
                  setGender(v === '미선택' ? null : (v as Gender));
                  setInvalid((s) => ({ ...s, gender: false }));
                }}
                options={GENDERS}
                invalid={invalid.gender}
                describedBy={invalid.gender ? 'gender-error' : undefined}
                ariaLabel="성별"
              />
            </Field>
          </div>

          <Field
            label="직업"
            hint="엔터를 누르면 등록됩니다"
            htmlFor="jobs"
            error={invalid.jobs ? '최소 2개가 필요합니다' : undefined}
          >
            <TokenInput
              id="jobs"
              value={jobs}
              onChange={(next) => {
                setJobs(next);
                setInvalid((s) => ({ ...s, jobs: false }));
              }}
              onDraftChange={() => setInvalid((s) => ({ ...s, jobs: false }))}
              placeholder="예: 간호사, 프리랜서 디자이너, 편의점 알바"
              max={TARGET_TOKEN_MAX}
              invalid={invalid.jobs}
              describedBy={invalid.jobs ? 'jobs-error' : undefined}
            />
          </Field>

          <Field
            label="장소"
            hint="엔터를 누르면 등록됩니다"
            htmlFor="places"
            error={invalid.places ? '최소 2개가 필요합니다' : undefined}
          >
            <TokenInput
              id="places"
              value={places}
              onChange={(next) => {
                setPlaces(next);
                setInvalid((s) => ({ ...s, places: false }));
              }}
              onDraftChange={() => setInvalid((s) => ({ ...s, places: false }))}
              placeholder="예: 사무실, 병원, 학교, 원룸"
              max={TARGET_TOKEN_MAX}
              invalid={invalid.places}
              describedBy={invalid.places ? 'places-error' : undefined}
            />
          </Field>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={submit}>
            문제 탐색 시작하기
            <ArrowRight size={18} aria-hidden />
          </Button>
        </div>
      </Page>
    </AppShell>
  );
}
