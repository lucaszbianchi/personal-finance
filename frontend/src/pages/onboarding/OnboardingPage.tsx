import React, { useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useOnboardingStatus } from '@/hooks/useOnboarding';
import { WelcomeStep } from './steps/WelcomeStep';
import { CredentialsStep } from './steps/CredentialsStep';
import { ConnectStep } from './steps/ConnectStep';
import { SyncStep } from './steps/SyncStep';
import { FeaturesGuideStep } from './steps/FeaturesGuideStep';
import { DoneStep } from './steps/DoneStep';

type StepEntry = {
  key: string;
  render: (onNext: () => void) => React.ReactNode;
};

type OnboardingMode = 'arrive' | 'restart' | 'review';

function buildSteps(mode: OnboardingMode, hasCredentials: boolean, hasPluggyItems: boolean): StepEntry[] {
  const isReview = mode === 'review';
  const skipCompleted = mode === 'restart' || mode === 'review';

  const allSteps: StepEntry[] = [
    { key: 'welcome', render: (onNext) => <WelcomeStep onNext={onNext} /> },
    { key: 'credentials', render: (onNext) => <CredentialsStep onNext={onNext} /> },
    { key: 'connect', render: (onNext) => <ConnectStep onNext={onNext} /> },
    { key: 'sync', render: (onNext) => <SyncStep onNext={onNext} skippable={isReview} /> },
    { key: 'features', render: (onNext) => <FeaturesGuideStep onNext={onNext} /> },
    { key: 'done', render: () => <DoneStep /> },
  ];

  if (!skipCompleted) return allSteps;

  return allSteps.filter((s) => {
    if (s.key === 'welcome') return false;
    if (s.key === 'credentials' && hasCredentials) return false;
    if (s.key === 'connect' && hasPluggyItems) return false;
    return true;
  });
}

export const OnboardingPage: React.FC = () => {
  const [step, setStep] = useState(0);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const mode = (searchParams.get('mode') as OnboardingMode) || 'arrive';
  const { data: status, isLoading } = useOnboardingStatus();

  const steps = useMemo(
    () =>
      buildSteps(
        mode,
        status?.has_credentials ?? false,
        status?.has_pluggy_items ?? false,
      ),
    [mode, status?.has_credentials, status?.has_pluggy_items],
  );

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <p className="text-gray-500">Carregando...</p>
      </div>
    );
  }

  if (status?.is_complete && mode === 'arrive') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
        <div className="w-full max-w-md rounded-xl bg-white p-8 shadow-lg text-center">
          <h2 className="text-xl font-bold text-gray-800 mb-3">Onboarding ja concluido</h2>
          <p className="text-gray-600 mb-6">
            Seus dados ja estao configurados. Voce pode acessar o dashboard normalmente.
          </p>
          <button
            onClick={() => navigate('/')}
            className="w-full rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-700 transition-colors"
          >
            Ir para o Dashboard
          </button>
        </div>
      </div>
    );
  }

  const onNext = () => setStep((prev) => Math.min(prev + 1, steps.length - 1));

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-md">
        {/* Progress indicator */}
        <div className="mb-6 flex items-center justify-center gap-2">
          {steps.map((_, i) => (
            <div
              key={i}
              className={`h-2 rounded-full transition-all ${
                i <= step ? 'w-8 bg-blue-600' : 'w-2 bg-gray-300'
              }`}
            />
          ))}
        </div>

        {/* Step content */}
        <div className="rounded-xl bg-white p-8 shadow-lg">
          {steps[step]?.render(onNext)}
        </div>
      </div>
    </div>
  );
};
