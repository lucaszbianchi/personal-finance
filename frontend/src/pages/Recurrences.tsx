import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { InstallmentsCard } from '@/components/InstallmentsCard';
import { FixedExpensesCard } from '@/components/FixedExpensesCard';
import { RecurrenceForm } from '@/components/RecurrenceForm';
import { RecurrenceDetail } from '@/components/RecurrenceDetail';
import { useRecurrenceYearly } from '@/hooks/useRecurrences';
import { MONTH_SHORT } from '@/constants/recurrences';
import type { Recurrence } from '@/types';

function currentYear(): number {
  return new Date().getFullYear();
}


const formatCurrency = (value: number) =>
  value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 2, maximumFractionDigits: 2 });

const formatYAxis = (v: number) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v);

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const parcelas = payload.find((p: any) => p.dataKey === 'Parcelas')?.value ?? 0;
  const fixas = payload.find((p: any) => p.dataKey === 'Contas fixas')?.value ?? 0;
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 text-sm min-w-[220px]">
      <p className="font-semibold text-gray-700 mb-2">{label}</p>
      <div className="space-y-1.5">
        <div className="flex justify-between gap-6">
          <span className="flex items-center gap-1.5 text-gray-600">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block" />
            Parcelamentos
          </span>
          <span>{formatCurrency(parcelas)}</span>
        </div>
        <div className="flex justify-between gap-6">
          <span className="flex items-center gap-1.5 text-gray-600">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-400 inline-block" />
            Contas fixas
          </span>
          <span>{formatCurrency(fixas)}</span>
        </div>
      </div>
      <div className="border-t border-gray-100 mt-3 pt-2 flex justify-between font-semibold">
        <span>Total</span>
        <span>{formatCurrency(parcelas + fixas)}</span>
      </div>
    </div>
  );
};

export const Recurrences: React.FC = () => {
  const [showForm, setShowForm] = useState(false);
  const [detailId, setDetailId] = useState<string | null>(null);
  const [editingRecurrence, setEditingRecurrence] = useState<Recurrence | null>(null);
  const { data: yearlyData, isLoading: yearlyLoading } = useRecurrenceYearly(currentYear());

  const year = currentYear();

  const chartData = (yearlyData ?? []).map((h) => ({
    month: MONTH_SHORT[parseInt(h.month.split('-')[1]) - 1],
    Parcelas: h.installments,
    'Contas fixas': h.fixed,
    projected: h.projected,
  }));

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Recorrencias</h1>

      {/* Yearly chart */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-gray-700">{year}</h2>
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block" />
              Parcelas
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-400 inline-block" />
              Contas fixas
            </span>
          </div>
        </div>
        {yearlyLoading ? (
          <div className="h-52 flex items-center justify-center text-gray-400 text-sm">
            Carregando...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }} barCategoryGap="30%" barGap={2}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
              <YAxis tickFormatter={formatYAxis} tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} width={32} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: '#f9fafb' }} />
              <Bar dataKey="Parcelas" radius={[3, 3, 0, 0]}>
                {chartData.map((entry, i) => (
                  <Cell key={i} fill="#fbbf24" fillOpacity={entry.projected ? 0.45 : 1} />
                ))}
              </Bar>
              <Bar dataKey="Contas fixas" radius={[3, 3, 0, 0]}>
                {chartData.map((entry, i) => (
                  <Cell key={i} fill="#60a5fa" fillOpacity={entry.projected ? 0.45 : 1} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Detail cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <InstallmentsCard />
        <FixedExpensesCard
          onAdd={() => setShowForm(true)}
          onItemClick={(id) => setDetailId(id)}
        />
      </div>

      {detailId && (
        <RecurrenceDetail
          id={detailId}
          onClose={() => setDetailId(null)}
          onEdit={(r) => { setDetailId(null); setEditingRecurrence(r); }}
        />
      )}
      {(showForm || editingRecurrence) && (
        <RecurrenceForm
          initial={editingRecurrence ?? undefined}
          onClose={() => { setShowForm(false); setEditingRecurrence(null); }}
        />
      )}
    </div>
  );
};
