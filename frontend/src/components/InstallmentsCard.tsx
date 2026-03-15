import React, { useState } from 'react';
import { MonthNavigator } from '@/components/MonthNavigator';
import { useRecurrenceInstallments } from '@/hooks/useRecurrences';

function currentMonth(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}

const formatCurrency = (value: number) =>
  value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

export const InstallmentsCard: React.FC = () => {
  const [month, setMonth] = useState(currentMonth());
  const { data: items = [], isLoading } = useRecurrenceInstallments(month);
  const isProjected = month > currentMonth();

  const total = items.reduce((acc, item) => acc + item.amount, 0);

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-gray-700">Parcelamentos</h3>
          {isProjected && (
            <span className="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded">
              projetado
            </span>
          )}
        </div>
        <MonthNavigator month={month} onChange={setMonth} />
      </div>

      {isLoading ? (
        <p className="text-gray-400 text-sm">Carregando...</p>
      ) : items.length === 0 ? (
        <p className="text-gray-400 text-sm">Nenhum parcelamento neste mes.</p>
      ) : (
        <>
          <div className="flex justify-end mb-3">
            <span className="text-sm font-medium text-blue-600">{formatCurrency(total)}</span>
          </div>
          <div className="space-y-3">
            {items.map((item) => {
              const instNum = item.installment_number ?? 0;
              const total_inst = item.total_installments ?? 1;
              const pct = Math.round((item.pct_paid ?? 0) * 100);
              return (
                <div key={item.id}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-700 truncate max-w-[60%]">{item.description}</span>
                    <span className="text-gray-500">
                      {instNum}/{total_inst} &middot; {formatCurrency(item.amount)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-1.5">
                    <div
                      className="bg-blue-500 h-1.5 rounded-full transition-all"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <div className="text-right text-xs text-gray-400 mt-0.5">{pct}% pago</div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
};
