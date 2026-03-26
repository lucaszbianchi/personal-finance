import React, { useEffect, useState } from 'react';
import { RefreshCw, CheckCircle, AlertCircle, AlertTriangle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useSyncData } from '@/hooks/useSyncData';
import { SyncCountCard } from '@/components/SyncCountCard';
import { importService, type ImportType, type RateLimitUsage } from '@/services/api';
import api from '@/services/api';

type PluggyItem = {
  item_id: string;
  connector_name?: string;
  alias?: string | null;
  role?: string;
};

const IMPORT_TYPE_LABELS: Record<ImportType, { label: string; description: string }> = {
  recent:     { label: 'Recente',   description: 'Últimos 7 dias' },
  non_recent: { label: 'Histórico', description: 'Até 365 dias atrás' },
};

function RateLimitBar({ usage, label }: { usage: RateLimitUsage | undefined; label: string }) {
  const count = usage?.count ?? 0;
  const limit = usage?.limit_value ?? (label === 'Recente' ? 120 : 4);
  const exceeded = usage?.exceeded ?? false;
  const remaining = limit - count;
  const pct = Math.min((count / limit) * 100, 100);

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-16 text-gray-500 shrink-0">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-1.5 overflow-hidden">
        <div
          className={`h-1.5 rounded-full transition-all ${
            exceeded ? 'bg-red-500' : remaining <= 1 ? 'bg-amber-400' : 'bg-blue-500'
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`w-14 text-right font-medium ${exceeded ? 'text-red-600' : 'text-gray-600'}`}>
        {count}/{limit}
      </span>
    </div>
  );
}

export const SyncPage: React.FC = () => {
  const { mutate: syncData, isPending, isSuccess, isError, data, error } = useSyncData();
  const [lastSyncTime, setLastSyncTime] = useState<string | null>(null);
  const [importType, setImportType] = useState<ImportType>('recent');
  const [syncingItemId, setSyncingItemId] = useState<string | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem('lastSyncTime');
    if (saved) setLastSyncTime(saved);
  }, []);

  useEffect(() => {
    if (isSuccess && data?.status === 'success') {
      setLastSyncTime(localStorage.getItem('lastSyncTime'));
      setSyncingItemId(null);
    }
  }, [isSuccess, data]);

  useEffect(() => {
    if (isError) setSyncingItemId(null);
  }, [isError]);

  const { data: items = [] } = useQuery<PluggyItem[]>({
    queryKey: ['pluggy', 'items'],
    queryFn: async () => {
      const response = await api.get('/pluggy/items');
      return response.data;
    },
  });

  const { data: rateLimitUsage = [] } = useQuery<RateLimitUsage[]>({
    queryKey: ['rate-limit-usage'],
    queryFn: () => importService.getRateLimitUsage(),
  });

  // Build lookup: item_id -> { recent, non_recent }
  const usageByItem = rateLimitUsage.reduce<Record<string, Record<string, RateLimitUsage>>>(
    (acc, u) => {
      if (!acc[u.item_id]) acc[u.item_id] = {};
      acc[u.item_id][u.call_type] = u;
      return acc;
    },
    {},
  );

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

  const handleSyncItem = (itemId: string) => {
    setSyncingItemId(itemId);
    syncData({ importType, itemId });
  };

  const handleSyncAll = () => {
    setSyncingItemId('all');
    syncData({ importType });
  };

  const counts = data?.counts;
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

  const bankItems = items.filter((item) => item.role === 'bank');

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">Sincronizar Dados</h1>
          <p className="text-gray-600">
            Atualize seus dados bancários, investimentos e contas compartilhadas
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          {/* Import type toggle */}
          <div className="mb-6">
            <p className="text-sm font-medium text-gray-700 mb-2">Tipo de sincronização</p>
            <div className="inline-flex rounded-lg border border-gray-200 p-1 bg-gray-50 gap-1">
              {(Object.keys(IMPORT_TYPE_LABELS) as ImportType[]).map((type) => (
                <button
                  key={type}
                  onClick={() => setImportType(type)}
                  disabled={isPending}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-150 ${
                    importType === type
                      ? 'bg-white text-blue-700 shadow-sm border border-gray-200'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {IMPORT_TYPE_LABELS[type].label}
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-1 ml-1">
              {IMPORT_TYPE_LABELS[importType].description}
              {importType === 'non_recent' && (
                <span className="ml-2 text-amber-600 font-medium">— limite de 4 sincronizações/mês por conta</span>
              )}
            </p>
          </div>

          {/* Per-item sync rows */}
          {bankItems.length > 0 && (
            <div className="mb-6">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                Contas conectadas
              </p>
              <div className="space-y-2">
                {bankItems.map((item) => {
                  const itemUsage = usageByItem[item.item_id] ?? {};
                  const isSyncingThis = isPending && syncingItemId === item.item_id;
                  const displayName = item.alias || item.connector_name || item.item_id.substring(0, 8) + '...';
                  return (
                    <div
                      key={item.item_id}
                      className="flex items-center gap-4 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-800 truncate">{displayName}</p>
                        <div className="mt-1.5 space-y-1">
                          <RateLimitBar usage={itemUsage['recent']} label="Recente" />
                          <RateLimitBar usage={itemUsage['non_recent']} label="Histórico" />
                        </div>
                      </div>
                      <button
                        onClick={() => handleSyncItem(item.item_id)}
                        disabled={isPending}
                        className={`shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                          isSyncingThis
                            ? 'bg-blue-100 text-blue-500 cursor-not-allowed'
                            : isPending
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : 'bg-blue-600 text-white hover:bg-blue-700 active:scale-95'
                        }`}
                      >
                        <RefreshCw size={14} className={isSyncingThis ? 'animate-spin' : ''} />
                        {isSyncingThis ? 'Sincronizando...' : 'Sincronizar'}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Sync All button */}
          <div className="mb-8">
            <button
              onClick={handleSyncAll}
              disabled={isPending}
              className={`w-full py-3 px-6 rounded-lg font-semibold text-white transition-all duration-200 flex items-center justify-center gap-2 ${
                isPending && syncingItemId === 'all'
                  ? 'bg-blue-400 cursor-not-allowed'
                  : isPending
                  ? 'bg-gray-300 cursor-not-allowed text-gray-500'
                  : 'bg-blue-600 hover:bg-blue-700 active:scale-95'
              }`}
            >
              <RefreshCw size={20} className={isPending && syncingItemId === 'all' ? 'animate-spin' : ''} />
              {isPending && syncingItemId === 'all' ? 'Sincronizando...' : 'Sincronizar Todos'}
            </button>
          </div>

          {/* Loading State (per-item) */}
          {isPending && syncingItemId && syncingItemId !== 'all' && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <p className="text-blue-800 text-center text-sm font-medium">
                Conectando com os bancos e serviços...
              </p>
            </div>
          )}

          {/* Success State */}
          {isSuccess && data?.status === 'success' && (
            <div className="space-y-6">
              {/* Rate limit warning */}
              {data.rate_limit_warning && (
                <div className="bg-amber-50 border border-amber-300 rounded-lg p-4 flex items-start gap-3">
                  <AlertTriangle size={20} className="text-amber-600 flex-shrink-0 mt-0.5" />
                  <p className="text-amber-800 text-sm">{data.rate_limit_warning}</p>
                </div>
              )}

              {/* Success Message */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-6 flex items-start gap-4">
                <CheckCircle size={24} className="text-green-600 flex-shrink-0 mt-1" />
                <div>
                  <h3 className="font-semibold text-green-800 text-lg">Sincronização Concluída!</h3>
                  <p className="text-green-700 mt-1">{data.message}</p>
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
                      <p className="text-3xl font-bold text-blue-700">{totalNew}</p>
                      <p className="text-sm text-blue-600 mt-1">Novos Itens</p>
                    </div>
                    <div className="text-center">
                      <p className="text-3xl font-bold text-indigo-700">{totalUpdated}</p>
                      <p className="text-sm text-indigo-600 mt-1">Atualizados</p>
                    </div>
                    <div className="text-center">
                      <p className="text-3xl font-bold text-purple-700">{totalNew + totalUpdated}</p>
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
                <h3 className="font-semibold text-red-800 text-lg">Erro na Sincronização</h3>
                <p className="text-red-700 mt-1">
                  Não foi possível sincronizar os dados. Tente novamente mais tarde.
                </p>
                <p className="text-sm text-red-600 mt-2 break-words">
                  {error instanceof Error ? error.message : 'Erro desconhecido'}
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
          <p className="text-blue-800 text-sm">
            A sincronização pode levar alguns minutos dependendo da quantidade de dados.
            Não feche esta página durante o processo.
          </p>
        </div>
      </div>
    </div>
  );
};

export default SyncPage;
