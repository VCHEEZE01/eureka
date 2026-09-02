import { permanentRedirect } from 'next/navigation';

/** 보관함이 마이페이지 하위로 옮겨져, 이전 경로는 새 위치로 넘긴다. */
export default function LegacyLibraryPage() {
  permanentRedirect('/mypage/library');
}
