import { PersonalizeFormScreen } from '@/screens/Personalize';

export default async function Page({ params }: { params: Promise<{ baseId: string }> }) {
  const { baseId } = await params;
  return <PersonalizeFormScreen baseId={baseId} />;
}
