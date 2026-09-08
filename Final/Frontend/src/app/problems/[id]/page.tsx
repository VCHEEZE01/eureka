import { ProblemDetailScreen } from '@/screens/ProblemDetail';

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ProblemDetailScreen problemId={id} />;
}
