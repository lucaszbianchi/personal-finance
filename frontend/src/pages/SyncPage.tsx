import React, { useEffect, useState } from 'react';
import { RefreshCw, CheckCircle, AlertCircle } from 'lucide-react';
import { useSyncData } from '@/hooks/useSyncData';
import { SyncCountCard } from '@/components/SyncCountCard';

export const SyncPage: React.FC = () => {
  const { mutate: syncData, isPending, isSuccess, isError, data, error } = useSyncData();
  const [lastSyncTime, setLastSyncTime] = useState<string | null>(null);

  useEffect(() => {
    // Carrega timestamp da última sincronização
    const saved = localStorage.getItem('lastSyncTime');
    if (saved) {
      setLastSyncTime(saved);
    }
  }, []);

  useEffect(() => {
    // Atualiza timestamp quando sincronização é bem-sucedida
    if (isSuccess && data?.status === 'success') {
      const now = new Date().toISOString();
      setLastSyncTime(now);
    }
  }, [isSuccess, data]);

  const handleSync = () => {
    syncData();
  };

  const formatDate = (isoString: string) => {
    return new Date(isoString).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const counts = data && typeof data === 'object' && 'counts' in data ? (data as any).counts : undefined;
  const totalNew = counts
    ? counts.bank_transactions_inserted +
      counts.credit_transactions_inserted +
      counts.investments_inserted +
      counts.splitwise_inserted
    : 0;

  const totalUpdated = counts
    ? counts.bank_transactions_updated +
      counts.credit_transactions_updated +
      counts.investments_updated +
      counts.splitwise_updated
    : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            Sincronizar Dados
          </h1>
          <p className="text-gray-600">
            Atualize seus dados bancários, investimentos e contas compartilhadas
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          {/* Button */}
          <div className="mb-8">
            <button
              onClick={handleSync}
              disabled={isPending}
              className={`w-full py-4 px-6 rounded-lg font-semibold text-white text-lg transition-all duration-200 flex items-center justify-center gap-2 ${
                isPending
                  ? 'bg-blue-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 active:scale-95'
              }`}
            >
              <RefreshCw
                size={24}
                className={isPending ? 'animate-spin' : ''}
              />
              {isPending ? 'Sincronizando...' : 'Sincronizar Agora'}
            </button>
          </div>

          {/* Loading State */}
          {isPending && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
              <p className="text-blue-800 text-center font-medium">
                Conectando com os bancos e serviços...
              </p>
            </div>
          )}

          {/* Success State */}
          {isSuccess && data?.status === 'success' && (
            <div className="space-y-6">
              {/* Success Message */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-6 flex items-start gap-4">
                <CheckCircle size={24} className="text-green-600 flex-shrink-0 mt-1" />
                <div>
                  <h3 className="font-semibold text-green-800 text-lg">
                    Sincronização Concluída!
                  </h3>
                  <p className="text-green-700 mt-1">
                    {data?.message}
                  </p>
                </div>
              </div>

              {/* Counts Grid */}
              {counts && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <SyncCountCard
                    title="Transações Bancárias"
                    inserted={counts.bank_transactions_inserted}
                    updated={counts.bank_transactions_updated}
                    colorScheme="emerald"
                  />
                  <SyncCountCard
                    title="Transações de Crédito"
                    inserted={counts.credit_transactions_inserted}
                    updated={counts.credit_transactions_updated}
                    colorScheme="sky"
                  />
                  <SyncCountCard
                    title="Investimentos"
                    inserted={counts.investments_inserted}
                    updated={counts.investments_updated}
                    colorScheme="amber"
                  />
                  <SyncCountCard
                    title="Splitwise"
                    inserted={counts.splitwise_inserted}
                    updated={counts.splitwise_updated}
                    colorScheme="violet"
                  />
                </div>
              )}

              {/* Totals */}
              {counts && (
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
                  <h4 className="font-semibold text-blue-900 mb-3">Resumo Total</h4>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <p className="text-3xl font-bold text-blue-700">
                        {totalNew}
                      </p>
                      <p className="text-sm text-blue-600 mt-1">Novos Itens</p>
                    </div>
                    <div className="text-center">
                      <p className="text-3xl font-bold text-indigo-700">
                        {totalUpdated}
                      </p>
                      <p className="text-sm text-indigo-600 mt-1">Atualizados</p>
                    </div>
                    <div className="text-center">
                      <p className="text-3xl font-bold text-purple-700">
                        {totalNew + totalUpdated}
                      </p>
                      <p className="text-sm text-purple-600 mt-1">Total</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Error State */}
          {isError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6 flex items-start gap-4">
              <AlertCircle size={24} className="text-red-600 flex-shrink-0 mt-1" />
              <div className="w-full">
                <h3 className="font-semibold text-red-800 text-lg">
                  Erro na Sincronização
                </h3>
                <p className="text-red-700 mt-1">
                  Não foi possível sincronizar os dados. Tente novamente mais tarde.
                </p>
                <p className="text-sm text-red-600 mt-2 break-words">
                  {error instanceof Error
                    ? error.message
                    : 'Erro desconhecido'}
                </p>
              </div>
            </div>
          )}

          {/* Last Sync Time */}
          {lastSyncTime && !isPending && (
            <div className="mt-8 pt-6 border-t border-gray-200 text-center">
              <p className="text-sm text-gray-600">
                <span className="font-medium">Última sincronização:</span>{' '}
                {formatDate(lastSyncTime)}
              </p>
            </div>
          )}
        </div>

        {/* Info Box */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
          <p className="text-blue-800">
            ℹ️ A sincronização pode levar alguns minutos dependendo da quantidade de dados.
            Não feche esta página durante o processo.
          </p>
        </div>
      </div>
    </div>
  );
};

export default SyncPage;
