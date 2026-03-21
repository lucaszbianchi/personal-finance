import React, { useEffect, useState } from 'react';
import { RefreshCw, CheckCircle, AlertCircle } from 'lucide-react';
import { useFullSync } from '@/hooks/useOnboarding';

const SYNC_MESSAGES = [
  'Inicializando banco de dados...',
  'Buscando categorias...',
  'Sincronizando transacoes historicas...',
  'Processando investimentos...',
  'Calculando historico financeiro...',
  'Quase la...',
];

type Props = { onNext: () => void };

export const SyncStep: React.FC<Props> = ({ onNext }) => {
  const { mutate, isPending, isSuccess, isError, error, data } = useFullSync();
  const [messageIndex, setMessageIndex] = useState(0);
  const [started, setStarted] = useState(false);

  useEffect(() => {
    if (!isPending) return;
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % SYNC_MESSAGES.length);
    }, 8000);
    return () => clearInterval(interval);
  }, [isPending]);

  const handleStart = () => {
    setStarted(true);
    mutate();
  };

  const monthsProcessed = data?.rebuild?.months_processed ?? 0;

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-800 mb-2">Sincronizar Dados</h2>
      <p className="text-sm text-gray-500 mb-6">
        Vamos importar ate 1 ano de dados financeiros. Isso pode levar alguns minutos.
      </p>

      {!started && (
        <button
          onClick={handleStart}
          className="w-full rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
        >
          <RefreshCw size={20} />
          Iniciar Sincronizacao
        </button>
      )}

      {isPending && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-6 text-center">
          <RefreshCw size={32} className="mx-auto mb-3 text-blue-600 animate-spin" />
          <p className="font-medium text-blue-800 mb-1">{SYNC_MESSAGES[messageIndex]}</p>
          <p className="text-xs text-blue-600">Nao feche esta pagina</p>
        </div>
      )}

      {isSuccess && data?.status === 'success' && (
        <div className="space-y-4">
          <div className="flex items-start gap-3 rounded-lg border border-green-200 bg-green-50 p-4">
            <CheckCircle size={20} className="mt-0.5 flex-shrink-0 text-green-600" />
            <div>
              <p className="font-semibold text-green-800">Sincronizacao concluida!</p>
              {monthsProcessed > 0 && (
                <p className="text-sm text-green-700 mt-1">
                  {monthsProcessed} {monthsProcessed === 1 ? 'mes processado' : 'meses processados'}
                </p>
              )}
            </div>
          </div>

          <button
            onClick={onNext}
            className="w-full rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-700 transition-colors"
          >
            Continuar
          </button>
        </div>
      )}

      {isError && (
        <div className="space-y-4">
          <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4">
            <AlertCircle size={20} className="mt-0.5 flex-shrink-0 text-red-600" />
            <div>
              <p className="font-semibold text-red-800">Erro na sincronizacao</p>
              <p className="text-sm text-red-700 mt-1">
                {error instanceof Error ? error.message : 'Erro desconhecido'}
              </p>
            </div>
          </div>

          <button
            onClick={handleStart}
            className="w-full rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-700 transition-colors"
          >
            Tentar Novamente
          </button>
        </div>
      )}
    </div>
  );
};
