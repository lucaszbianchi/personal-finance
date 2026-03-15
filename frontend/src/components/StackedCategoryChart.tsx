import React, { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { formatCurrency, shortMonth, chartTickFormatter } from '@/utils/format';
import type { CashFlowMonthCategories } from '@/hooks/useCashFlow';

const COLORS = [
  '#3b82f6', '#f59e0b', '#10b981', '#8b5cf6',
  '#ef4444', '#06b6d4', '#f97316', '#ec4899',
];

const MAX_CATEGORIES = 7;

interface Props {
  data: CashFlowMonthCategories[];
}


export const StackedCategoryChart: React.FC<Props> = ({ data }) => {
  const { topCategories, chartData } = useMemo(() => {
    const totals: Record<string, number> = {};
    for (const entry of data) {
      for (const [cat, val] of Object.entries(entry.categories)) {
        totals[cat] = (totals[cat] ?? 0) + val;
      }
    }

    const sorted = Object.entries(totals)
      .sort((a, b) => b[1] - a[1])
      .map(([name]) => name);

    const top = sorted.slice(0, MAX_CATEGORIES);
    const hasOthers = sorted.length > MAX_CATEGORIES;
    const categories = hasOthers ? [...top, 'Outros'] : top;

    const rows = data.map((entry) => {
      const row: Record<string, string | number> = { month: shortMonth(entry.month) };
      let othersTotal = 0;

      for (const [cat, val] of Object.entries(entry.categories)) {
        if (top.includes(cat)) {
          row[cat] = val;
        } else {
          othersTotal += val;
        }
      }

      if (hasOthers) {
        row['Outros'] = Math.round(othersTotal * 100) / 100;
      }

      return row;
    });

    return { topCategories: categories, chartData: rows };
  }, [data]);

  if (topCategories.length === 0) {
    return (
      <p className="text-gray-500 text-center py-8 text-sm">
        Nenhum dado de categorias disponivel
      </p>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={chartData} margin={{ top: 10, right: 16, left: 10, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="month" tick={{ fontSize: 11 }} />
        <YAxis tickFormatter={chartTickFormatter} tick={{ fontSize: 11 }} width={60} />
        <Tooltip
          formatter={(value: number, name: string) => [formatCurrency(value), name]}
        />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {topCategories.map((cat, i) => (
          <Bar
            key={cat}
            dataKey={cat}
            stackId="a"
            fill={COLORS[i % COLORS.length]}
            radius={i === topCategories.length - 1 ? [3, 3, 0, 0] : undefined}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
};
