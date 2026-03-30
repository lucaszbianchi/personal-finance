import React, { useState } from 'react';
import { KeyRound, AlertCircle, ExternalLink } from 'lucide-react';
import { useSaveCredentials } from '@/hooks/useOnboarding';

type Props = { onNext: () => void };

export const CredentialsStep: React.FC<Props> = ({ onNext }) => {
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const { mutate, isPending, isError, error } = useSaveCredentials();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutate(
      { client_id: clientId, client_secret: clientSecret },
      { onSuccess: onNext },
    );
  };

  const errorMessage = isError
    ? (error as Error & { response?: { data?: { error?: string } } })?.response?.data?.error
      || 'Erro ao salvar credenciais'
    : null;

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
          <KeyRound size={20} className="text-blue-600" />
        </div>
        <h2 className="text-xl font-bold text-gray-800">Credenciais da Pluggy</h2>
      </div>

      <div className="mb-6 rounded-lg border border-blue-100 bg-blue-50 p-4 text-sm text-gray-700 space-y-2">
        <p className="font-medium text-blue-800">Como obter suas credenciais:</p>
        <ol className="list-decimal list-inside space-y-1 text-gray-600">
          <li>
            Crie uma conta de desenvolvedor em{' '}
            <a
              href="https://dashboard.pluggy.ai"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 underline inline-flex items-center gap-0.5"
            >
              dashboard.pluggy.ai <ExternalLink size={12} />
            </a>
          </li>
          <li>
            Acesse{' '}
            <a
              href="https://dashboard.pluggy.ai/applications"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 underline inline-flex items-center gap-0.5"
            >
              Applications <ExternalLink size={12} />
            </a>
            {' '}e crie uma nova aplicacao (o nome pode ser qualquer um)
          </li>
          <li>Copie o <strong>Client ID</strong> e o <strong>Client Secret</strong> exibidos</li>
          <li>
            Em{' '}
            <a
              href="https://dashboard.pluggy.ai/customization"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 underline inline-flex items-center gap-0.5"
            >
              Customization <ExternalLink size={12} />
            </a>
            , habilite o conector <strong>MeuPluggy</strong> em Connectors {'>'} Personal {'>'} Direct Connectors e salve
          </li>
        </ol>
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
