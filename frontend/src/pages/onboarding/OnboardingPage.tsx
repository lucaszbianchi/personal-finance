import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useOnboardingStatus } from '@/hooks/useOnboarding';
import { WelcomeStep } from './steps/WelcomeStep';
import { CredentialsStep } from './steps/CredentialsStep';
import { ConnectStep } from './steps/ConnectStep';
import { SyncStep } from './steps/SyncStep';
import { DoneStep } from './steps/DoneStep';

const STEP_COUNT = 5;

export const OnboardingPage: React.FC = () => {
  const [step, setStep] = useState(0);
  const navigate = useNavigate();
  const { data: status, isLoading } = useOnboardingStatus();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <p className="text-gray-500">Carregando...</p>
      </div>
    );
  }

  if (status?.is_complete) {
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

  const onNext = () => setStep((prev) => Math.min(prev + 1, STEP_COUNT - 1));

  const steps: Record<number, React.ReactNode> = {
    0: <WelcomeStep onNext={onNext} />,
    1: <CredentialsStep onNext={onNext} />,
    2: <ConnectStep onNext={onNext} />,
    3: <SyncStep onNext={onNext} />,
    4: <DoneStep />,
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-md">
        {/* Progress indicator */}
        <div className="mb-6 flex items-center justify-center gap-2">
          {Array.from({ length: STEP_COUNT }).map((_, i) => (
            <div
              key={i}
              className={`h-2 rounded-full transition-all ${
                i <= step ? 'w-8 bg-blue-600' : 'w-2 bg-gray-300'
              }`}
            />
          ))}
        </div>

        {/* Step content */}
        <div className="rounded-xl bg-white p-8 shadow-lg">{steps[step]}</div>
      </div>
    </div>
  );
};
