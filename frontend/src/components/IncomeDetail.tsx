import React, { useState } from 'react';
import { useIncomeDetail, useDeleteIncomeSource } from '@/hooks/useIncome';
import { FREQUENCY_LABELS, MONTH_SHORT } from '@/constants/recurrences';
import type { IncomeSource } from '@/types';

interface Props {
  id: string;
  onClose: () => void;
  onEdit: (s: IncomeSource) => void;
}


function formatHeaderDate(dateStr: string | null): string {
  if (!dateStr) return '-';
  const d = new Date(dateStr.slice(0, 10) + 'T12:00:00');
  return d.toLocaleDateString('pt-BR', { weekday: 'short', day: 'numeric', month: 'long' });
}

function formatShortDate(dateStr: string): string {
  const [y, m, day] = dateStr.split('-');
  return `${parseInt(day)} ${MONTH_SHORT[parseInt(m) - 1]} ${y.slice(2)}`;
}

function formatCurrency(value: number | null): string {
  if (value == null) return '-';
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

export const IncomeDetail: React.FC<Props> = ({ id, onClose, onEdit }) => {
  const { data, isLoading } = useIncomeDetail(id);
  const deleteSource = useDeleteIncomeSource();
  const [confirmDelete, setConfirmDelete] = useState(false);

  const handleDelete = async () => {
    await deleteSource.mutateAsync(id);
    onClose();
  };

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black bg-opacity-30" onClick={onClose} />
      <div className="fixed right-0 top-0 z-50 h-full w-96 bg-white shadow-xl overflow-y-auto flex flex-col">
        {isLoading || !data ? (
          <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
            Carregando...
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="p-5 border-b border-gray-100">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-gray-900 truncate">
                    {data.source.description}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {formatHeaderDate(data.metrics.last_received_date)}
                  </p>
                </div>
                <div className="flex items-center gap-2 ml-3 shrink-0">
                  <button
                    onClick={() => onEdit(data.source)}
                    title="Editar"
                    className="text-gray-400 hover:text-blue-600 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => setConfirmDelete(true)}
                    title="Apagar"
                    className="text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                  <button
                    onClick={onClose}
                    title="Fechar"
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              {confirmDelete && (
                <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between gap-3">
                  <p className="text-sm text-red-700">Apagar esta receita recorrente?</p>
                  <div className="flex gap-2 shrink-0">
                    <button
                      onClick={() => setConfirmDelete(false)}
                      className="text-xs text-gray-500 hover:text-gray-700 transition-colors"
                    >
                      Cancelar
                    </button>
                    <button
                      onClick={handleDelete}
                      disabled={deleteSource.isPending}
                      className="text-xs bg-red-600 text-white px-2 py-1 rounded hover:bg-red-700 transition-colors disabled:opacity-50"
                    >
                      Apagar
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Rules */}
            <div className="p-5 border-b border-gray-100">
              <div className="border border-gray-200 rounded-lg p-4 bg-gray-50 space-y-2 text-sm">
                <p className="font-medium text-gray-700 mb-1">Regras</p>
                {data.source.merchant_name && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Nome contém</span>
                    <span className="text-gray-800 font-medium">{data.source.merchant_name}</span>
                  </div>
                )}
                {(data.source.amount_min != null || data.source.amount_max != null) && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Valor</span>
                    <span className="text-gray-800 font-medium">
                      {data.source.amount_min != null ? formatCurrency(data.source.amount_min) : 'qualquer'}
                      {' - '}
                      {data.source.amount_max != null ? formatCurrency(data.source.amount_max) : 'qualquer'}
                    </span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-500">Frequencia</span>
                  <span className="text-gray-800 font-medium">
                    {FREQUENCY_LABELS[data.source.frequency ?? ''] ?? data.source.frequency ?? '-'}
                  </span>
                </div>
              </div>
            </div>

            {/* Timeline */}
            <div className="p-5 border-b border-gray-100">
              <p className="text-sm font-medium text-gray-700 mb-3">Ultimos 12 meses</p>
              <div className="flex gap-1.5">
                {data.timeline.map((entry) => {
                  const monthIdx = parseInt(entry.month.split('-')[1]) - 1;
                  return (
                    <div key={entry.month} className="flex-1 flex flex-col items-center gap-1">
                      <div
                        className={`w-full h-7 rounded ${entry.matched ? 'bg-green-400' : 'bg-gray-200'}`}
                        title={entry.month}
                      />
                      <span className="text-xs text-gray-400">{MONTH_SHORT[monthIdx][0]}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Metrics */}
            <div className="p-5 border-b border-gray-100">
              <p className="text-sm font-medium text-gray-700 mb-3">Metricas</p>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="border border-gray-100 rounded-lg p-3">
                  <p className="text-xs text-gray-400">Ultimo valor</p>
                  <p className="font-semibold text-gray-800 mt-0.5">{formatCurrency(data.metrics.last_amount)}</p>
                </div>
                <div className="border border-gray-100 rounded-lg p-3">
                  <p className="text-xs text-gray-400">Media</p>
                  <p className="font-semibold text-gray-800 mt-0.5">{formatCurrency(data.metrics.avg_amount)}</p>
                </div>
                <div className="border border-gray-100 rounded-lg p-3">
                  <p className="text-xs text-gray-400">Total no ano</p>
                  <p className="font-semibold text-green-600 mt-0.5">{formatCurrency(data.metrics.total_this_year)}</p>
                </div>
                <div className="border border-gray-100 rounded-lg p-3">
                  <p className="text-xs text-gray-400">Proximo esperado</p>
                  <p className="font-semibold text-gray-800 mt-0.5">
                    {data.source.next_occurrence ? formatShortDate(data.source.next_occurrence) : '-'}
                  </p>
                </div>
              </div>
            </div>

            {/* Linked transactions */}
            <div className="p-5 flex-1">
              <p className="text-sm font-medium text-gray-700 mb-3">
                Transações Vinculadas ({data.linked_transactions.length})
              </p>
              {data.linked_transactions.length === 0 ? (
                <p className="text-sm text-gray-400">Nenhuma transação encontrada.</p>
              ) : (
                <div className="space-y-1">
                  {data.linked_transactions.map((txn) => (
                    <div
                      key={txn.id}
                      className="flex items-center justify-between py-1.5 border-b border-gray-50 last:border-0 text-sm"
                    >
                      <div className="flex-1 min-w-0">
                        <span className="text-xs text-gray-400 block">{formatShortDate(txn.date)}</span>
                        <span className="text-gray-700 truncate block">{txn.description}</span>
                      </div>
                      <span className="text-green-600 font-medium ml-3 shrink-0">
                        {formatCurrency(txn.amount)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </>
  );
};
