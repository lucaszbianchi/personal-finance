import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { CategoryBreakdownItem } from '@/types';
import { formatCurrency } from '@/utils/format';

const COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6b7280',
];

interface Props {
  data: CategoryBreakdownItem[];
}


export const CategoryPieChart: React.FC<Props> = ({ data }) => {
  const positive = data.filter(d => d.total > 0).slice(0, 10);
  const total = positive.reduce((s, d) => s + d.total, 0);

  const chartData = positive.map(d => ({
    name: d.description,
    value: Math.round(d.total * 100) / 100,
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={55}
          outerRadius={100}
          paddingAngle={2}
          dataKey="value"
        >
          {chartData.map((entry, index) => (
            <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value: number) => [
            `${formatCurrency(value)} (${total > 0 ? ((value / total) * 100).toFixed(1) : 0}%)`,
            'Gasto',
          ]}
        />
        <Legend iconType="circle" iconSize={10} formatter={(v) => <span className="text-xs">{v}</span>} />
      </PieChart>
    </ResponsiveContainer>
  );
};
