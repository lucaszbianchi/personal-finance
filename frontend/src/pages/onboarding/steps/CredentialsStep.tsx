import React, { useState } from 'react';
import { KeyRound, AlertCircle } from 'lucide-react';
import { useSaveCredentials } from '@/hooks/useOnboarding';

type Props = { onNext: () => void };

export const CredentialsStep: React.FC<Props> = ({ onNext }) => {
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [splitwiseAccountName, setSplitwiseAccountName] = useState('');
  const { mutate, isPending, isError, error } = useSaveCredentials();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutate(
      {
        client_id: clientId,
        client_secret: clientSecret,
        ...(splitwiseAccountName ? { splitwise_account_name: splitwiseAccountName } : {}),
      },
      { onSuccess: onNext },
    );
  };

  const errorMessage = isError
    ? (error as Error & { response?: { data?: { error?: string } } })?.response?.data?.error
      || 'Erro ao salvar credenciais'
    : null;

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
          <KeyRound size={20} className="text-blue-600" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-800">Credenciais da Pluggy</h2>
          <p className="text-sm text-gray-500">
            Crie uma conta em{' '}
            <a
              href="https://pluggy.ai"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 underline"
            >
              pluggy.ai
            </a>{' '}
            e obtenha suas credenciais
          </p>
        </div>
      </div>

      {errorMessage && (
        <div className="mb-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3">
          <AlertCircle size={16} className="mt-0.5 flex-shrink-0 text-red-600" />
          <p className="text-sm text-red-700">{errorMessage}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="clientId" className="block text-sm font-medium text-gray-700 mb-1">
            Client ID
          </label>
          <input
            id="clientId"
            type="text"
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            required
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
            placeholder="Seu Client ID da Pluggy"
          />
        </div>

        <div>
          <label htmlFor="clientSecret" className="block text-sm font-medium text-gray-700 mb-1">
            Client Secret
          </label>
          <input
            id="clientSecret"
            type="password"
            value={clientSecret}
            onChange={(e) => setClientSecret(e.target.value)}
            required
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
            placeholder="Seu Client Secret da Pluggy"
          />
        </div>

        <div>
          <label htmlFor="splitwise" className="block text-sm font-medium text-gray-700 mb-1">
            Nome da conta Splitwise{' '}
            <span className="text-gray-400 font-normal">(opcional)</span>
          </label>
          <input
            id="splitwise"
            type="text"
            value={splitwiseAccountName}
            onChange={(e) => setSplitwiseAccountName(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
            placeholder="Ex: Splitwise"
          />
        </div>

        <button
          type="submit"
          disabled={isPending || !clientId || !clientSecret}
          className="w-full rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
        >
          {isPending ? 'Salvando...' : 'Salvar e Continuar'}
        </button>
      </form>
    </div>
  );
};
