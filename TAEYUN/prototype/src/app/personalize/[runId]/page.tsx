import { PersonalizeResultScreen } from '@/screens/Personalize';

export default async function Page({ params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  return <PersonalizeResultScreen id={runId} />;
}
