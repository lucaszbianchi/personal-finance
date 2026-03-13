import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts';
import type { SpendingPaceDayEntry } from '@/types';
import { formatCurrency } from '@/utils/format';

interface Props {
  dailySeries: SpendingPaceDayEntry[];
  monthlyGoal: number | null;
  monthlyAvg: number | null;
  unavoidableAvg: number | null;
  currentMonthLabel?: string;
  prevMonthLabel?: string;
}

const tickFormatter = (value: number) =>
  value >= 1000 ? `R$${(value / 1000).toFixed(0)}k` : `R$${value}`;

export const SpendingPaceChart: React.FC<Props> = ({
  dailySeries,
  monthlyGoal,
  monthlyAvg,
  unavoidableAvg,
  currentMonthLabel = 'Mês atual',
  prevMonthLabel = 'Mês anterior',
}) => {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={dailySeries} margin={{ top: 10, right: 16, left: 10, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />

        <XAxis
          dataKey="day"
          tick={{ fontSize: 11 }}
          label={{ value: 'Dia', position: 'insideBottomRight', offset: -4, fontSize: 11 }}
        />
        <YAxis
          tickFormatter={tickFormatter}
          tick={{ fontSize: 11 }}
          width={56}
        />

        <Tooltip
          formatter={(value: number, name: string) => [formatCurrency(value), name]}
          labelFormatter={(day: number) => `Dia ${day}`}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />

        {/* Current month — solid primary blue */}
        <Line
          type="monotone"
          dataKey="cumulative_amount"
          name={currentMonthLabel}
          stroke="#3b82f6"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
        />

        {/* Previous month — dashed gray */}
        <Line
          type="monotone"
          dataKey="prev_month_cumulative"
          name={prevMonthLabel}
          stroke="#9ca3af"
          strokeWidth={1.5}
          strokeDasharray="5 4"
          dot={false}
          activeDot={{ r: 3 }}
        />

        {/* Monthly goal — red reference line */}
        {monthlyGoal != null && (
          <ReferenceLine
            y={monthlyGoal}
            stroke="#ef4444"
            strokeDasharray="6 3"
            label={{ value: 'Meta', position: 'insideTopRight', fill: '#ef4444', fontSize: 11 }}
          />
        )}

        {/* 6-month historical average — blue reference line */}
        {monthlyAvg != null && (
          <ReferenceLine
            y={monthlyAvg}
            stroke="#3b82f6"
            strokeDasharray="6 3"
            strokeOpacity={0.5}
            label={{ value: 'Média 6m', position: 'insideTopRight', fill: '#3b82f6', fontSize: 11 }}
          />
        )}

        {/* Unavoidable recurring average — orange reference line (placeholder for S4) */}
        {unavoidableAvg != null && (
          <ReferenceLine
            y={unavoidableAvg}
            stroke="#f97316"
            strokeDasharray="6 3"
            label={{ value: 'Inevitáveis', position: 'insideTopRight', fill: '#f97316', fontSize: 11 }}
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
};
