import React from 'react';
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { formatCurrency, shortMonth, chartTickFormatter } from '@/utils/format';
import type { CashFlowMonthValue } from '@/hooks/useCashFlow';

interface Props {
  currentData: CashFlowMonthValue[];
  previousData: CashFlowMonthValue[];
  label: string;
}

export const CashFlowBarChart: React.FC<Props> = ({ currentData, previousData, label }) => {
  const data = currentData.map((cur, i) => ({
    month: shortMonth(cur.month),
    current: cur.value,
    previous: previousData[i]?.value ?? null,
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <ComposedChart data={data} margin={{ top: 10, right: 16, left: 10, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="month" tick={{ fontSize: 11 }} />
        <YAxis tickFormatter={chartTickFormatter} tick={{ fontSize: 11 }} width={60} />
        <Tooltip
          formatter={(value, name) => [
            value != null ? formatCurrency(value as number) : 'N/A',
            name === 'current' ? label : 'Periodo anterior',
          ]}
        />
        <Legend
          formatter={(value) => (value === 'current' ? label : 'Periodo anterior')}
          wrapperStyle={{ fontSize: 12 }}
        />
        <Bar dataKey="current" name="current" radius={[3, 3, 0, 0]}>
          {data.map((entry, index) => (
            <Cell
              key={index}
              fill={(entry.current ?? 0) >= 0 ? '#10b981' : '#ef4444'}
            />
          ))}
        </Bar>
        <Line
          type="monotone"
          dataKey="previous"
          name="previous"
          stroke="#9ca3af"
          strokeWidth={1.5}
          strokeDasharray="5 4"
          dot={false}
          activeDot={{ r: 3 }}
          connectNulls
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
};
