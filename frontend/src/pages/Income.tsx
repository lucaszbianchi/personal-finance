import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { TooltipProps } from 'recharts';
import type { ValueType, NameType } from 'recharts/types/component/DefaultTooltipContent';
import { IncomeForm } from '@/components/IncomeForm';
import { IncomeDetail } from '@/components/IncomeDetail';
import { useIncomeYearly, useIncomeMonthly } from '@/hooks/useIncome';
import { MONTH_SHORT, MONTH_LONG } from '@/constants/recurrences';
import type { IncomeSource } from '@/types';

function currentMonth(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}


const formatCurrency = (value: number) =>
  value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 2, maximumFractionDigits: 2 });

const formatYAxis = (v: number) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v);

const CustomTooltip = ({ active, payload, label }: TooltipProps<ValueType, NameType>) => {
  if (!active || !payload?.length) return null;
  const total = Number(payload[0]?.value ?? 0);
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 text-sm min-w-[180px]">
      <p className="font-semibold text-gray-700 mb-2">{label}</p>
      <div className="flex justify-between gap-4">
        <span className="flex items-center gap-1.5 text-gray-600">
          <span className="w-2.5 h-2.5 rounded-full bg-green-400 inline-block" />
          Receitas Recorrentes
        </span>
        <span>{formatCurrency(total)}</span>
      </div>
    </div>
  );
};

function prevMonth(month: string): string {
  const [y, m] = month.split('-').map(Number);
  const d = new Date(y, m - 2, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

function nextMonth(month: string): string {
  const [y, m] = month.split('-').map(Number);
  const d = new Date(y, m, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

function monthLabel(month: string): string {
  const [y, m] = month.split('-').map(Number);
  return `${MONTH_LONG[m - 1]} de ${y}`;
}

export const Income: React.FC = () => {
  const [selectedMonth, setSelectedMonth] = useState(currentMonth());
  const [showForm, setShowForm] = useState(false);
  const [editingSource, setEditingSource] = useState<IncomeSource | null>(null);
  const [detailId, setDetailId] = useState<string | null>(null);

  const selectedYear = parseInt(selectedMonth.split('-')[0]);
  const { data: yearlyData, isLoading: yearlyLoading } = useIncomeYearly(selectedYear);
  const { data: monthlyData } = useIncomeMonthly(selectedMonth);

  const chartData = (yearlyData ?? []).map((h) => ({
    month: MONTH_SHORT[parseInt(h.month.split('-')[1]) - 1],
    monthKey: h.month,
    total: h.total,
  }));

  const selectedMonthIndex = parseInt(selectedMonth.split('-')[1]) - 1;
  const selectedTotal = yearlyData?.find((h) => h.month === selectedMonth)?.total ?? 0;

  const handleBarClick = (data: { activePayload?: Array<{ payload?: { monthKey?: string } }> } | null) => {
    if (data?.activePayload?.[0]?.payload?.monthKey) {
      setSelectedMonth(data.activePayload[0].payload.monthKey);
    }
  };

  const items = monthlyData?.sources?.items ?? [];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Receitas Recorrentes</h1>
        <button
          onClick={() => setShowForm(true)}
          className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Nova Receita Recorrente
        </button>
      </div>

      {/* Yearly chart */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-gray-700">{selectedYear}</h2>
          <span className="flex items-center gap-1.5 text-xs text-gray-500">
            <span className="w-2.5 h-2.5 rounded-full bg-green-400 inline-block" />
            Receitas Recorrentes
          </span>
        </div>
        <div className="flex gap-4">
          <div className="flex-1">
            {yearlyLoading ? (
              <div className="h-52 flex items-center justify-center text-gray-400 text-sm">
                Carregando...
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart
                  data={chartData}
                  margin={{ top: 5, right: 10, left: 0, bottom: 5 }}
                  barCategoryGap="30%"
                  onClick={handleBarClick}
                  style={{ cursor: 'pointer' }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
                  <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
                  <YAxis tickFormatter={formatYAxis} tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} width={32} />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: '#f9fafb' }} />
                  <Bar dataKey="total" fill="#4ade80" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
          <div className="w-36 flex flex-col items-center justify-center border-l border-gray-100 pl-4">
            <p className="text-xs text-gray-500 text-center">{MONTH_LONG[selectedMonthIndex]}</p>
            <p className="text-xs text-gray-400 mt-1">Total</p>
            <p className="text-base font-bold text-green-600 mt-0.5">{formatCurrency(selectedTotal)}</p>
          </div>
        </div>
      </div>

      {/* Monthly list */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-end mb-4">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <button
              onClick={() => setSelectedMonth(prevMonth(selectedMonth))}
              className="p-1 hover:text-gray-900 transition-colors"
            >
              &lt;
            </button>
            <span className="font-medium capitalize">{monthLabel(selectedMonth)}</span>
            <button
              onClick={() => setSelectedMonth(nextMonth(selectedMonth))}
              className="p-1 hover:text-gray-900 transition-colors"
            >
              &gt;
            </button>
          </div>
        </div>

        {items.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-8">
            Nenhuma receita recorrente para este mês.
          </p>
        ) : (
          <div className="space-y-2">
            {items.map((source) => (
              <button
                key={source.id}
                onClick={() => setDetailId(source.id)}
                className="w-full flex items-center justify-between px-3 py-2 rounded-md hover:bg-gray-50 text-left"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded bg-green-100 flex items-center justify-center text-sm text-green-700 font-medium">
                    $
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-800">
                      {source.description ?? source.merchant_name ?? '-'}
                    </p>
                    <span className="text-xs text-gray-400">
                      {source.frequency === 'monthly' ? 'Mensal' : source.frequency === 'annual' ? 'Anual' : source.frequency ?? ''}
                      {source.next_occurrence ? ` · prox. ${source.next_occurrence}` : ''}
                    </span>
                  </div>
                </div>
                <span className="text-sm font-semibold text-green-600 shrink-0">
                  {formatCurrency(source.amount ?? 0)}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {detailId && (
        <IncomeDetail
          id={detailId}
          onClose={() => setDetailId(null)}
          onEdit={(s) => { setDetailId(null); setEditingSource(s); }}
        />
      )}
      {(showForm || editingSource) && (
        <IncomeForm
          initial={editingSource ?? undefined}
          onClose={() => { setShowForm(false); setEditingSource(null); }}
        />
      )}
    </div>
  );
};
