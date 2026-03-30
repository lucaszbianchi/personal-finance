import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Link2, CheckCircle, Trash2, AlertCircle, ExternalLink } from 'lucide-react';
import { PluggyConnectButton } from '@/components/PluggyConnectButton';
import { AliasModal } from '@/components/AliasModal';
import api from '@/services/api';

type PluggyItem = {
  item_id: string;
  connector_name?: string;
  alias?: string | null;
  role?: string;
};

type PendingItem = {
  id: string;
  connector_name?: string;
};

type Props = { onNext: () => void };

export const ConnectStep: React.FC<Props> = ({ onNext }) => {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [pendingItem, setPendingItem] = useState<PendingItem | null>(null);
  const [pendingAlias, setPendingAlias] = useState('');

  const { data: items = [] } = useQuery<PluggyItem[]>({
    queryKey: ['pluggy', 'items'],
    queryFn: async () => {
      const response = await api.get('/pluggy/items');
      return response.data;
    },
  });

  const handleConnectSuccess = (item: {
    id: string;
    connector?: { name?: string };
  }) => {
    setError(null);
    setPendingItem({ id: item.id, connector_name: item.connector?.name });
    setPendingAlias('');
  };

  const handleSavePendingItem = async (alias: string) => {
    if (!pendingItem) return;
    try {
      await api.post('/pluggy/items', {
        item_id: pendingItem.id,
        connector_name: pendingItem.connector_name,
        status: 'CONNECTED',
        alias: alias.trim() || undefined,
      });
      queryClient.invalidateQueries({ queryKey: ['pluggy', 'items'] });
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'status'] });
    } catch {
      setError('Erro ao salvar item. Tente novamente.');
    } finally {
      setPendingItem(null);
      setPendingAlias('');
    }
  };

  const handleRemoveItem = async (id: string) => {
    try {
      await api.delete(`/pluggy/items/${id}`);
      queryClient.invalidateQueries({ queryKey: ['pluggy', 'items'] });
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'status'] });
    } catch {
      setError('Erro ao remover item');
    }
  };

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
          <Link2 size={20} className="text-blue-600" />
        </div>
        <h2 className="text-xl font-bold text-gray-800">Conectar Contas</h2>
      </div>

      <div className="mb-6 rounded-lg border border-blue-100 bg-blue-50 p-4 text-sm text-gray-700 space-y-2">
        <p className="font-medium text-blue-800">Como conectar:</p>
        <ol className="list-decimal list-inside space-y-1 text-gray-600">
          <li>
            Acesse{' '}
            <a
              href="https://meu.pluggy.ai/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 underline inline-flex items-center gap-0.5"
            >
              meu.pluggy.ai <ExternalLink size={12} />
            </a>
            {' '}e crie sua conta
          </li>
          <li>
            Em{' '}
            <a
              href="https://meu.pluggy.ai/connections"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 underline inline-flex items-center gap-0.5"
            >
              Conexoes <ExternalLink size={12} />
            </a>
            , crie suas conexoes (contas bancarias, corretoras)
          </li>
          <li>Clique em <strong>"Conectar conta"</strong> abaixo para abrir o widget</li>
          <li>Faca login com sua conta do <strong>meu.pluggy.ai</strong></li>
          <li>Selecione a instituicao e autorize o acesso</li>
        </ol>
        <p className="text-gray-500 mt-2">
          Voce pode conectar varias contas. Repita o processo para cada instituicao.
        </p>
      </div>

      <div className="mb-4">
        <PluggyConnectButton
          onSuccess={handleConnectSuccess}
          label="Conectar conta"
        />
      </div>

      {error && (
        <div className="mb-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3">
          <AlertCircle size={16} className="mt-0.5 flex-shrink-0 text-red-600" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Connected items list */}
      {items.length > 0 && (
        <div className="mb-6 space-y-1">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Contas conectadas</p>
          {items.map((item) => (
            <div
              key={item.item_id}
              className="flex items-center justify-between rounded-lg border border-green-200 bg-green-50 px-4 py-2"
            >
              <div className="flex items-center gap-2">
                <CheckCircle size={16} className="text-green-600" />
                <span className="text-sm text-green-800">
                  {item.alias || item.connector_name || item.item_id.substring(0, 8) + '...'}
                </span>
              </div>
              <button
                onClick={() => handleRemoveItem(item.item_id)}
                className="text-gray-400 hover:text-red-500 transition-colors"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}

      <button
        onClick={onNext}
        disabled={items.length === 0}
        className="w-full rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
      >
        Continuar
      </button>

      {items.length === 0 && (
        <p className="mt-2 text-center text-xs text-gray-400">
          Conecte pelo menos uma conta para continuar
        </p>
      )}

      {/* Modal: Nome da nova conta conectada */}
      {pendingItem && (
        <AliasModal
          alias={pendingAlias}
          onChange={setPendingAlias}
          onSave={handleSavePendingItem}
        />
      )}
    </div>
  );
};
