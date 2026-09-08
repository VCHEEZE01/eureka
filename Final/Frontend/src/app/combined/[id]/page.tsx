import { CombinedDetailScreen } from '@/screens/Combine';

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <CombinedDetailScreen combinedId={id} />;
}
