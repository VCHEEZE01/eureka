import { IdeaDetailScreen } from '@/screens/Ideas';

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <IdeaDetailScreen ideaId={id} />;
}
