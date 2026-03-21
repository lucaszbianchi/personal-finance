import React from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Link2, CheckCircle } from 'lucide-react';
import { PluggyConnectButton } from '@/components/PluggyConnectButton';
import api from '@/services/api';

type PluggyItem = {
  item_id: string;
  connector_name?: string;
  role?: string;
};

type Props = { onNext: () => void };

export const ConnectStep: React.FC<Props> = ({ onNext }) => {
  const queryClient = useQueryClient();

  const { data: items = [] } = useQuery<PluggyItem[]>({
    queryKey: ['pluggy', 'items'],
    queryFn: async () => {
      const response = await api.get('/pluggy/items');
      return response.data;
    },
  });

  const bankItems = items.filter((i) => i.role === 'bank');

  const handleItemConnected = async (item: { id: string; connector?: { name?: string } }) => {
    await api.post('/pluggy/items', {
      item_id: item.id,
      connector_name: item.connector?.name,
      status: 'CONNECTED',
    });
    queryClient.invalidateQueries({ queryKey: ['pluggy', 'items'] });
    queryClient.invalidateQueries({ queryKey: ['onboarding', 'status'] });
  };

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
          <Link2 size={20} className="text-blue-600" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-800">Conectar Conta Bancaria</h2>
          <p className="text-sm text-gray-500">
            Use o widget da Pluggy para conectar sua instituicao financeira
          </p>
        </div>
      </div>

      {bankItems.length > 0 && (
        <div className="mb-6 space-y-2">
          <p className="text-sm font-medium text-gray-700">Contas conectadas:</p>
          {bankItems.map((item) => (
            <div
              key={item.item_id}
              className="flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-3"
            >
              <CheckCircle size={16} className="text-green-600" />
              <span className="text-sm text-green-800">
                {item.connector_name || item.item_id}
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="mb-6">
        <PluggyConnectButton onSuccess={handleItemConnected} />
      </div>

      <button
        onClick={onNext}
        disabled={bankItems.length === 0}
        className="w-full rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
      >
        Continuar
      </button>

      {bankItems.length === 0 && (
        <p className="mt-2 text-center text-xs text-gray-400">
          Conecte pelo menos uma conta bancaria para continuar
        </p>
      )}
    </div>
  );
};
