import React from 'react';
import { useRecurrenceMonthly } from '@/hooks/useRecurrences';

interface Props {
  onAdd: () => void;
  onItemClick: (id: string) => void;
}

const formatCurrency = (value: number | null) =>
  value != null
    ? value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
    : '-';

const FREQUENCY_LABELS: Record<string, string> = {
  monthly: 'Mensal',
  annual: 'Anual',
  weekly: 'Semanal',
};

export const FixedExpensesCard: React.FC<Props> = ({ onAdd, onItemClick }) => {
  const currentMonth = `${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, '0')}`;
  const { data: monthly } = useRecurrenceMonthly(currentMonth);

  const items = monthly?.fixed_expenses.items ?? [];
  const total = monthly?.fixed_expenses.total ?? 0;

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-gray-700">Despesas Fixas</h3>
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-emerald-600">{formatCurrency(total)}</span>
          <button
            onClick={onAdd}
            className="text-xs bg-emerald-500 text-white px-2 py-1 rounded hover:bg-emerald-600 transition-colors"
          >
            + Adicionar
          </button>
        </div>
      </div>

      {items.length === 0 ? (
        <p className="text-gray-400 text-sm">Nenhuma despesa fixa cadastrada.</p>
      ) : (
        <div className="space-y-2">
          {items.map((item) => (
            <div key={item.id} className="flex items-center justify-between py-1 border-b border-gray-50 last:border-0">
              <div className="flex-1 min-w-0">
                <button
                  onClick={() => onItemClick(item.id)}
                  className="text-sm text-gray-800 truncate hover:text-blue-600 cursor-pointer text-left block w-full"
                >
                  {item.description}
                </button>
                <div className="text-xs text-gray-400">
                  {FREQUENCY_LABELS[item.frequency ?? ''] ?? item.frequency}
                  {item.next_occurrence ? ` · prox. ${item.next_occurrence}` : ''}
                </div>
              </div>
              <span className="text-sm font-medium text-gray-700 ml-2 shrink-0">
                {formatCurrency(item.amount)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
