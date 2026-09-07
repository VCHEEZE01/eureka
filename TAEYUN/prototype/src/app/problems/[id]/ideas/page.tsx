import { BasicIdeasScreen } from '@/screens/Ideas';

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <BasicIdeasScreen problemId={id} />;
}
