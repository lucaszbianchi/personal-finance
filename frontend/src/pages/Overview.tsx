import React, { useState } from 'react';
import { useSpendingPace } from '@/hooks/useSpendingPace';
import { useNetWorth, usePartialResult } from '@/hooks/useNetWorth';
import { SpendingPaceChart } from '@/components/SpendingPaceChart';
import { NetWorthCard } from '@/components/NetWorthCard';
import { PartialResultCard } from '@/components/PartialResultCard';
import { MonthNavigator } from '@/components/MonthNavigator';

const MONTH_NAMES = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
];

function currentYearMonth(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}

function prevYearMonth(ym: string): string {
  const [y, m] = ym.split('-').map(Number);
  const d = new Date(y, m - 2, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

function monthLabel(ym: string): string {
  const [y, m] = ym.split('-').map(Number);
  return `${MONTH_NAMES[m - 1]} ${y}`;
}

export const Overview: React.FC = () => {
  const [paceMonth, setPaceMonth] = useState(currentYearMonth);
  const today = currentYearMonth();

  const { data: pace, isLoading } = useSpendingPace(paceMonth);
  const { data: netWorthData, isLoading: isNetWorthLoading } = useNetWorth();
  const { data: partialResultData, isLoading: isPartialLoading } = usePartialResult();

  const paceDelta: number | null = (() => {
    const series = pace?.daily_series;
    if (!series || series.length === 0) return null;
    const todayDay = new Date().getDate();
    const idx = paceMonth === currentYearMonth()
      ? Math.min(todayDay, series.length) - 1
      : series.length - 1;
    const entry = series[idx];
    if (!entry || entry.prev_month_cumulative === 0) return null;
    return ((entry.cumulative_amount - entry.prev_month_cumulative) / entry.prev_month_cumulative) * 100;
  })();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Visão Geral</h2>
        <p className="text-gray-600">Acompanhamento consolidado das suas finanças</p>
      </div>

      {/* Patrimônio e Resultado Parcial */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {isNetWorthLoading ? (
          <div className="bg-white rounded-lg shadow p-6 flex items-center justify-center h-40">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
          </div>
        ) : netWorthData ? (
          <NetWorthCard data={netWorthData} />
        ) : null}
        {isPartialLoading ? (
          <div className="bg-white rounded-lg shadow p-6 flex items-center justify-center h-40">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
          </div>
        ) : partialResultData ? (
          <PartialResultCard data={partialResultData} />
        ) : null}
      </div>

      {/* Spending Pace */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              Ritmo de Gastos
              {paceDelta != null && (
                <span
                  className={`ml-2 text-sm font-normal ${paceDelta <= 0 ? 'text-green-600' : 'text-red-500'}`}
                >
                  {paceDelta > 0 ? '+' : ''}{paceDelta.toFixed(1)}% vs mês anterior
                </span>
              )}
            </h3>
            <p className="text-xs text-gray-500 mt-0.5">
              Gasto acumulado dia a dia — {monthLabel(paceMonth)} vs {monthLabel(prevYearMonth(paceMonth))}
            </p>
          </div>
          <MonthNavigator month={paceMonth} onChange={setPaceMonth} maxMonth={today} />
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
          </div>
        ) : pace?.daily_series && pace.daily_series.length > 0 ? (
          <SpendingPaceChart
            dailySeries={pace.daily_series}
            monthlyGoal={pace.monthly_goal}
            monthlyAvg={pace.monthly_avg}
            unavoidableAvg={pace.unavoidable_avg}
            currentMonthLabel={monthLabel(paceMonth)}
            prevMonthLabel={monthLabel(prevYearMonth(paceMonth))}
          />
        ) : (
          <p className="text-gray-500 text-center py-8 text-sm">
            Nenhum dado de transações disponível para este período
          </p>
        )}
      </div>
    </div>
  );
};
