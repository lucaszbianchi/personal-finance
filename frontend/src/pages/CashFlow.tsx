import React, { useState, useMemo } from 'react';
import { useCashFlow } from '@/hooks/useCashFlow';
import { useCategories } from '@/hooks/useCategories';
import { useCategoryLabelByName } from '@/hooks/useCategoryLabel';
import { CashFlowBarChart } from '@/components/CashFlowBarChart';
import { StackedCategoryChart } from '@/components/StackedCategoryChart';
import { formatCurrency } from '@/utils/format';
import type { Category } from '@/types';

function currentYearMonth(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}

function DeltaBadge({ delta, invertColors = false }: { delta: number | null; invertColors?: boolean }) {
  if (delta == null) return null;
  const isPositive = delta > 0;
  const isGood = invertColors ? !isPositive : isPositive;
  return (
    <span className={`ml-2 text-sm font-normal ${isGood ? 'text-green-600' : 'text-red-500'}`}>
      {isPositive ? '+' : ''}{delta.toFixed(1)}% vs periodo anterior
    </span>
  );
}

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-48">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
    </div>
  );
}

export const CashFlow: React.FC = () => {
  const [period, setPeriod] = useState<3 | 6>(3);
  const [endMonth, setEndMonth] = useState(currentYearMonth);

  const { data, isLoading } = useCashFlow(period, endMonth);
  const { data: categories } = useCategories();

  const catByDescription = useMemo(() => {
    const map = new Map<string, Category>();
    (categories ?? []).forEach((c) => map.set(c.description, c));
    return map;
  }, [categories]);

  const getCategoryLabel = useCategoryLabelByName(catByDescription);

  const translatedExpenses = useMemo(() => {
    if (!data) return [];
    return data.current_window.expenses_by_category.map((entry) => ({
      month: entry.month,
      categories: Object.fromEntries(
        Object.entries(entry.categories).map(([desc, total]) => [getCategoryLabel(desc), total]),
      ),
    }));
  }, [data, getCategoryLabel]);

  const deltaExpenses = (() => {
    if (!data) return null;
    const curTotal = data.current_window.period_total;
    const prevTotal = data.previous_window.period_total;
    if (curTotal == null || prevTotal == null || prevTotal === 0) return null;
    const curExp = data.current_window.expenses_by_category.reduce(
      (sum, e) => sum + Object.values(e.categories).reduce((s, v) => s + v, 0),
      0,
    );
    const prevIncome = data.previous_window.income.reduce((s, e) => s + (e.value ?? 0), 0);
    const prevExp = prevIncome - prevTotal;
    if (prevExp === 0) return null;
    return Math.round(((curExp - prevExp) / Math.abs(prevExp)) * 1000) / 10;
  })();

  const deltaIncome = (() => {
    if (!data) return null;
    const cur = data.current_window.income.reduce((s, e) => s + (e.value ?? 0), 0);
    const prev = data.previous_window.income.reduce((s, e) => s + (e.value ?? 0), 0);
    if (prev === 0) return null;
    return Math.round(((cur - prev) / Math.abs(prev)) * 1000) / 10;
  })();

  const totalExpenses = data
    ? data.current_window.expenses_by_category.reduce(
        (sum, e) => sum + Object.values(e.categories).reduce((s, v) => s + v, 0),
        0,
      )
    : null;

  const totalIncome = data
    ? data.current_window.income.reduce((s, e) => s + (e.value ?? 0), 0)
    : null;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Fluxo de Caixa</h2>
          <p className="text-gray-600">Analise de receitas e despesas por periodo</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex rounded-md border border-gray-300 overflow-hidden">
            <button
              onClick={() => setPeriod(3)}
              className={`px-3 py-1.5 text-sm font-medium transition-colors ${
                period === 3
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              3 meses
            </button>
            <button
              onClick={() => setPeriod(6)}
              className={`px-3 py-1.5 text-sm font-medium transition-colors border-l border-gray-300 ${
                period === 6
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              6 meses
            </button>
          </div>
          <input
            type="month"
            value={endMonth}
            max={currentYearMonth()}
            onChange={(e) => e.target.value && setEndMonth(e.target.value)}
            className="border border-gray-300 rounded-md px-2 py-1.5 text-sm text-gray-700"
          />
        </div>
      </div>

      {/* Resultado Liquido */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="mb-4">
          <h3 className="text-lg font-medium text-gray-900 uppercase tracking-wide">
            Resultado Liquido
            {data && <DeltaBadge delta={data.previous_window.delta_pct} />}
          </h3>
          {data && (
            <p className="text-2xl font-bold mt-1">
              {formatCurrency(data.current_window.period_total ?? 0)}
            </p>
          )}
        </div>
        {isLoading ? (
          <LoadingSpinner />
        ) : data ? (
          <CashFlowBarChart
            currentData={data.current_window.net_balance}
            previousData={data.previous_window.net_balance}
            label="Resultado"
          />
        ) : (
          <p className="text-gray-500 text-center py-8 text-sm">Nenhum dado disponivel</p>
        )}
      </div>

      {/* Gastos + Receitas */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Gastos */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="mb-4">
            <h3 className="text-lg font-medium text-gray-900 uppercase tracking-wide">
              Gastos
              {deltaExpenses != null && <DeltaBadge delta={deltaExpenses} invertColors />}
            </h3>
            {data && (
              <p className="text-2xl font-bold mt-1">
                {formatCurrency(totalExpenses ?? 0)}
              </p>
            )}
          </div>
          {isLoading ? (
            <LoadingSpinner />
          ) : translatedExpenses.length > 0 ? (
            <StackedCategoryChart data={translatedExpenses} />
          ) : (
            <p className="text-gray-500 text-center py-8 text-sm">Nenhum dado disponivel</p>
          )}
        </div>

        {/* Receitas */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="mb-4">
            <h3 className="text-lg font-medium text-gray-900 uppercase tracking-wide">
              Receitas
              {deltaIncome != null && <DeltaBadge delta={deltaIncome} />}
            </h3>
            {data && (
              <p className="text-2xl font-bold mt-1">
                {formatCurrency(totalIncome ?? 0)}
              </p>
            )}
          </div>
          {isLoading ? (
            <LoadingSpinner />
          ) : data ? (
            <CashFlowBarChart
              currentData={data.current_window.income}
              previousData={data.previous_window.income}
              label="Receita"
            />
          ) : (
            <p className="text-gray-500 text-center py-8 text-sm">Nenhum dado disponivel</p>
          )}
        </div>
      </div>
    </div>
  );
};
