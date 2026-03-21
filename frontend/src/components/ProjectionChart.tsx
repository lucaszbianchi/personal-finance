import React from 'react';
import {
  ComposedChart,
  Bar,
  Cell,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts';
import { formatCurrency, chartTickFormatter } from '@/utils/format';
import type { ProjectionHistoryMonth, ProjectionMonth } from '@/types';

interface Props {
  history: ProjectionHistoryMonth[];
  projection: ProjectionMonth[];
}

interface ChartEntry {
  month: string;
  type: 'actual' | 'projected';
  income: number;
  fixed: number;
  installments: number;
  variable: number;
  net_worth_actual: number | null;
  net_worth_projected: number | null;
}

function shortMonthYear(ym: string): string {
  const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
  const [year, m] = ym.split('-').map(Number);
  return `${months[m - 1]}/${String(year).slice(2)}`;
}

export const ProjectionChart: React.FC<Props> = ({ history, projection }) => {
  const historyEntries: ChartEntry[] = history.map((entry, idx) => ({
    month: shortMonthYear(entry.month),
    type: 'actual',
    income: entry.income,
    fixed: entry.fixed,
    installments: entry.installments,
    variable: entry.variable,
    net_worth_actual: entry.net_worth,
    // Bridge: last history point also anchors the projection line so the two connect
    net_worth_projected: idx === history.length - 1 ? entry.net_worth : null,
  }));

  const projectionEntries: ChartEntry[] = projection.map(entry => ({
    month: shortMonthYear(entry.month),
    type: 'projected',
    income: entry.income,
    fixed: entry.fixed,
    installments: entry.installments,
    variable: entry.variable,
    net_worth_actual: null,
    net_worth_projected: entry.net_worth,
  }));

  const chartData = [...historyEntries, ...projectionEntries];

  const today = new Date();
  const currentMonthKey = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
  const currentMonthLabel = shortMonthYear(currentMonthKey);

  const LABELS: Record<string, string> = {
    income: 'Receitas',
    fixed: 'Gastos Fixos',
    installments: 'Parcelas',
    variable: 'Gastos Variaveis',
    net_worth_actual: 'Patrimonio Real',
    net_worth_projected: 'Projecao Patrimonio',
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={chartData} margin={{ top: 10, right: 16, left: 10, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="month" tick={{ fontSize: 11 }} />
        <YAxis tickFormatter={chartTickFormatter} tick={{ fontSize: 11 }} width={64} />
        <Tooltip
          formatter={(value, name) => [
            formatCurrency(value as number),
            LABELS[name as string] ?? name,
          ]}
        />
        <Legend
          formatter={(value) => LABELS[value] ?? value}
          wrapperStyle={{ fontSize: 12 }}
        />
        <ReferenceLine
          x={currentMonthLabel}
          stroke="#9ca3af"
          strokeDasharray="4 4"
          label={{ value: 'Hoje', fontSize: 11, fill: '#9ca3af' }}
        />

        {/* Income bar */}
        <Bar dataKey="income" name="income" fill="#10b981" radius={[3, 3, 0, 0]}>
          {chartData.map((entry, index) => (
            <Cell key={index} fill="#10b981" fillOpacity={entry.type === 'actual' ? 1 : 0.5} />
          ))}
        </Bar>

        {/* Stacked expense bars: fixed → installments → variable */}
        <Bar dataKey="fixed" name="fixed" stackId="expenses" fill="#ef4444">
          {chartData.map((entry, index) => (
            <Cell key={index} fill="#ef4444" fillOpacity={entry.type === 'actual' ? 1 : 0.5} />
          ))}
        </Bar>
        <Bar dataKey="installments" name="installments" stackId="expenses" fill="#f97316">
          {chartData.map((entry, index) => (
            <Cell key={index} fill="#f97316" fillOpacity={entry.type === 'actual' ? 1 : 0.5} />
          ))}
        </Bar>
        <Bar dataKey="variable" name="variable" stackId="expenses" fill="#a855f7" radius={[3, 3, 0, 0]}>
          {chartData.map((entry, index) => (
            <Cell key={index} fill="#a855f7" fillOpacity={entry.type === 'actual' ? 1 : 0.5} />
          ))}
        </Bar>

        {/* Net worth: blue for actual history, gray dashed for projection */}
        <Line
          type="linear"
          dataKey="net_worth_actual"
          name="net_worth_actual"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
          connectNulls={false}
        />
        <Line
          type="linear"
          dataKey="net_worth_projected"
          name="net_worth_projected"
          stroke="#9ca3af"
          strokeWidth={2}
          strokeDasharray="5 3"
          dot={false}
          activeDot={{ r: 4 }}
          connectNulls={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
};
