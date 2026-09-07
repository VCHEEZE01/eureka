import { PersonalizedIdeaDetailScreen } from '@/screens/Personalize';

export default async function Page({
  params,
}: {
  params: Promise<{ runId: string; ideaId: string }>;
}) {
  const { runId, ideaId } = await params;
  return <PersonalizedIdeaDetailScreen id={runId} ideaId={ideaId} />;
}
