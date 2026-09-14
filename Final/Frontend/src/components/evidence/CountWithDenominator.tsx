'use client';

/**
 * "12건 / 판정된 40건 중" 형태.
 * ★ total 을 필수 prop으로 둬서, 분모 없이 건수만 렌더하는 사용을 막는다.
 *   (DATA_SPEC 4절: 분모 없는 건수는 화면에서 반드시 오해된다)
 */
export function CountWithDenominator({
  value,
  total,
  unit = '건',
  totalLabel = '판정된',
}: {
  value: number;
  total: number;
  unit?: string;
  totalLabel?: string;
}) {
  return (
    <span className="text-[15px]">
      <b className="text-text-primary">
        {value}
        {unit}
      </b>
      <span className="text-text-secondary">
        {' '}
        / {totalLabel} {total}
        {unit} 중
      </span>
    </span>
  );
}
