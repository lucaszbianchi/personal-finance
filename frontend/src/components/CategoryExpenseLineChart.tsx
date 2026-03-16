import React, { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useCategoryExpenseHistory } from '@/hooks/useCategoryVisualization';
import { formatCurrency, shortMonth } from '@/utils/format';

const MAX_SELECTED = 6;

const COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6b7280',
];

const MONTHS_OPTIONS = [
  { value: 6, label: '6 meses' },
  { value: 12, label: '12 meses' },
];

export const CategoryExpenseLineChart: React.FC = () => {
  const [months, setMonths] = useState(6);
  const { data, isLoading } = useCategoryExpenseHistory(months);
  const [selected, setSelected] = useState<string[]>([]);

  // Auto-select top 6 on first load or when data changes
  useEffect(() => {
    if (data?.series && data.series.length > 0) {
      setSelected(data.series.slice(0, MAX_SELECTED).map(s => s.id));
    }
  }, [data?.series.map(s => s.id).join(',')]);

  const toggleCategory = (id: string) => {
    setSelected(prev =>
      prev.includes(id)
        ? prev.filter(x => x !== id)
        : prev.length < MAX_SELECTED
          ? [...prev, id]
          : prev
    );
  };

  const selectedSeries = (data?.series ?? []).filter(s => selected.includes(s.id));

  const chartData = (data?.months ?? []).map((month, idx) => ({
    month,
    ...Object.fromEntries(selectedSeries.map(s => [s.id, s.data[idx] ?? 0])),
  }));

  const colorFor = (id: string) => {
    const idx = selected.indexOf(id);
    return COLORS[idx >= 0 ? idx : 0];
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Gastos por Categoria ao Longo do Tempo</h3>
        <select
          value={months}
          onChange={e => setMonths(Number(e.target.value))}
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-primary-500 focus:border-primary-500"
        >
          {MONTHS_OPTIONS.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {/* Category selector chips */}
      {data && data.series.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-5">
          {data.series.map((s) => {
            const isActive = selected.includes(s.id);
            const isDisabled = !isActive && selected.length >= MAX_SELECTED;
            const color = isActive ? COLORS[selected.indexOf(s.id)] : '#d1d5db';
            return (
              <button
                key={s.id}
                onClick={() => toggleCategory(s.id)}
                disabled={isDisabled}
                style={{ borderColor: color, color: isActive ? color : '#6b7280' }}
                className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                  isActive ? 'bg-opacity-10' : 'bg-white'
                } disabled:opacity-40 disabled:cursor-not-allowed`}
              >
                {s.name}
              </button>
            );
          })}
          <span className="text-xs text-gray-400 self-center ml-1">
            (máx. {MAX_SELECTED} simultâneas)
          </span>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600" />
        </div>
      ) : chartData.length === 0 ? (
        <p className="text-gray-500 text-center py-12">Sem dados disponíveis.</p>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="month"
              tickFormatter={m => shortMonth(m)}
              tick={{ fontSize: 12 }}
            />
            <YAxis
              tickFormatter={v => `R$${v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v}`}
              tick={{ fontSize: 12 }}
              width={55}
            />
            <Tooltip
              formatter={(value: number, name: string) => {
                const s = data?.series.find(x => x.id === name);
                return [formatCurrency(value), s?.name ?? name];
              }}
              labelFormatter={label => shortMonth(String(label))}
            />
            <Legend
              formatter={id => {
                const s = data?.series.find(x => x.id === id);
                return s?.name ?? id;
              }}
            />
            {selectedSeries.map(s => (
              <Line
                key={s.id}
                type="monotone"
                dataKey={s.id}
                stroke={colorFor(s.id)}
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};
