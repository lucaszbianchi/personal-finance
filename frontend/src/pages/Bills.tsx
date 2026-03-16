import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { MonthNavigator } from '@/components/MonthNavigator';
import { useBillsMonthly, useBillsHistory } from '@/hooks/useBills';
import { formatCurrency } from '@/utils/format';
import type { BillClassification } from '@/types';

function currentYearMonth(): string {
  return new Date().toISOString().slice(0, 7);
}

const LABEL: Record<BillClassification, string> = {
  installment: 'Parcela',
  recurrent: 'Recorrente',
  one_off: 'Avulso',
};

const BADGE_CLASS: Record<BillClassification, string> = {
  installment: 'bg-blue-100 text-blue-700',
  recurrent: 'bg-purple-100 text-purple-700',
  one_off: 'bg-gray-100 text-gray-600',
};

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-48">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
    </div>
  );
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return `${String(d.getUTCDate()).padStart(2, '0')}/${String(d.getUTCMonth() + 1).padStart(2, '0')}`;
}

function shortMonth(ym: string): string {
  const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
  const m = parseInt(ym.slice(5, 7), 10);
  return months[m - 1];
}

export const Bills: React.FC = () => {
  const [month, setMonth] = useState(currentYearMonth);

  const { data, isLoading } = useBillsMonthly(month);
  const { data: history } = useBillsHistory();

  const chartData = (history ?? []).slice(-6).map(e => ({
    month: shortMonth(e.month),
    total: e.total,
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Faturas</h1>
          {data && (
            <p className="text-4xl font-bold text-gray-900 mt-1">
              {formatCurrency(data.total)}
            </p>
          )}
          {data?.is_projected && (
            <p className="text-sm text-gray-400 mt-1">Projecao</p>
          )}
          {!data?.is_projected && data?.is_open === true && (
            <p className="text-sm text-yellow-600 mt-1">Fatura em aberto</p>
          )}
          {!data?.is_projected && data?.is_open === false && data.payment_date && (
            <p className="text-sm text-green-600 mt-1">
              Paga em {formatDate(data.payment_date)}
            </p>
          )}
        </div>
        <MonthNavigator month={month} onChange={setMonth} />
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <>
          {/* Breakdown card */}
          <div className="bg-white rounded-lg shadow p-4 divide-y divide-gray-100">
            <div className="flex justify-between py-3">
              <span className="text-gray-600">Parcelas</span>
              <span className="font-semibold text-gray-900">{formatCurrency(data?.installments ?? 0)}</span>
            </div>
            <div className="flex justify-between py-3">
              <span className="text-gray-600">Recorrentes</span>
              <span className="font-semibold text-gray-900">{formatCurrency(data?.recurrent ?? 0)}</span>
            </div>
            <div className="flex justify-between py-3">
              <span className="text-gray-600">Compras avulsas</span>
              <span className="font-semibold text-gray-900">{formatCurrency(data?.one_off ?? 0)}</span>
            </div>
          </div>

          {/* History chart */}
          {chartData.length > 0 && (
            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="text-sm font-medium text-gray-500 mb-3">Historico (6 meses)</h2>
              <ResponsiveContainer width="100%" height={100}>
                <LineChart data={chartData}>
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis hide />
                  <Tooltip
                    formatter={(v: number) => [formatCurrency(v), 'Total']}
                    contentStyle={{ fontSize: 12 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="total"
                    stroke="#4f46e5"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Transaction table */}
          {data && data.transactions.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Descricao</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Classificacao</th>
                    <th className="text-right px-4 py-3 font-medium text-gray-500">Valor</th>
                    <th className="text-right px-4 py-3 font-medium text-gray-500">Data</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.transactions.map(tx => (
                    <tr key={tx.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-gray-900 max-w-xs truncate">
                        {tx.description ?? '-'}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${BADGE_CLASS[tx.classification]}`}>
                          {LABEL[tx.classification]}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-medium text-gray-900">
                        {formatCurrency(tx.amount)}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-500">
                        {tx.date ? formatDate(tx.date) : '--/--'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {data && data.transactions.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              Nenhuma transacao encontrada para este periodo.
            </div>
          )}
        </>
      )}
    </div>
  );
};
