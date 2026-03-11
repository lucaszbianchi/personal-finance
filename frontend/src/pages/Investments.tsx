import React from 'react';
import { TrendingUp } from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useInvestments, useInvestmentHistory } from '@/hooks/useInvestments';
import type { Investment, InvestmentHistoryEntry } from '@/types';

const TYPE_LABELS: Record<string, string> = {
  FIXED_INCOME: 'Renda Fixa',
  SECURITY: 'Previdência',
  MUTUAL_FUND: 'Fundos',
  EQUITY: 'Renda Variável',
  ETF: 'ETF',
  COE: 'COE',
  OTHER: 'Outros',
};

const TYPE_COLORS: Record<string, string> = {
  FIXED_INCOME: '#3b82f6',
  SECURITY: '#8b5cf6',
  MUTUAL_FUND: '#f59e0b',
  EQUITY: '#10b981',
  ETF: '#06b6d4',
  COE: '#f97316',
  OTHER: '#6b7280',
};

const formatCurrency = (value: number | null | undefined) =>
  (value ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

const formatDate = (value: string | null | undefined) =>
  value ? value.slice(0, 10) : '—';

type SubtypeGroup = { subtype: string; items: Investment[] };
type TypeGroup = { type: string; subtypes: SubtypeGroup[] };

function groupInvestments(list: Investment[]): TypeGroup[] {
  // Preserve insertion order for both type and subtype
  const typeOrder: string[] = [];
  const typeMap: Record<string, Record<string, Investment[]>> = {};

  for (const inv of list) {
    const t = inv.type ?? 'OTHER';
    const s = inv.subtype ?? '—';
    if (!typeMap[t]) {
      typeMap[t] = {};
      typeOrder.push(t);
    }
    if (!typeMap[t][s]) typeMap[t][s] = [];
    typeMap[t][s].push(inv);
  }

  return typeOrder.map(t => ({
    type: t,
    subtypes: Object.entries(typeMap[t]).map(([s, items]) => ({ subtype: s, items })),
  }));
}

const formatCurrencyShort = (value: number) => {
  if (value >= 1_000_000) return `R$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `R$${(value / 1_000).toFixed(0)}K`;
  return formatCurrency(value);
};

const HistoryChart: React.FC<{ history: InvestmentHistoryEntry[] }> = ({ history }) => {
  // Collect all types across all entries
  const allTypes = Array.from(
    new Set(history.flatMap(e => Object.keys(e.by_type)))
  );

  // Sort chronologically (history comes DESC from API)
  const chartData = [...history]
    .sort((a, b) => a.month.localeCompare(b.month))
    .map(entry => ({
      month: entry.month,
      ...Object.fromEntries(allTypes.map(t => [t, entry.by_type[t] ?? 0])),
    }));

  if (chartData.length === 0) return null;

  return (
    <section className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Evolução Mensal por Tipo</h3>
      <ResponsiveContainer width="100%" height={320}>
        <AreaChart data={chartData} margin={{ top: 4, right: 16, left: 16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="month" tick={{ fontSize: 12 }} />
          <YAxis tickFormatter={formatCurrencyShort} tick={{ fontSize: 12 }} width={72} />
          <Tooltip
            formatter={(value: number, name: string) => [
              formatCurrency(value),
              TYPE_LABELS[name] ?? name,
            ]}
          />
          <Legend formatter={(name) => TYPE_LABELS[name] ?? name} />
          {allTypes.map(t => (
            <Area
              key={t}
              type="monotone"
              dataKey={t}
              stackId="1"
              stroke={TYPE_COLORS[t] ?? '#6b7280'}
              fill={TYPE_COLORS[t] ?? '#6b7280'}
              fillOpacity={0.7}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </section>
  );
};

export const Investments: React.FC = () => {
  const { data: investments, isLoading, error } = useInvestments();
  const { data: history } = useInvestmentHistory();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        Erro ao carregar investimentos.
      </div>
    );
  }

  const list = investments ?? [];
  const totalGross = list.reduce((sum, i) => sum + (i.amount ?? 0), 0);
  const totalNet = list.reduce((sum, i) => sum + (i.balance ?? 0), 0);
  const groups = groupInvestments(list);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Investimentos</h2>
          <p className="text-gray-600">Acompanhe o desempenho dos seus investimentos</p>
        </div>
        <TrendingUp className="w-8 h-8 text-primary-600" />
      </div>

      {/* Total summary */}
      <div className="grid grid-cols-2 gap-4">
        <SummaryCard label="Total bruto" value={totalGross} highlight />
        <SummaryCard label="Total líquido" value={totalNet} highlight />
      </div>

      {/* Historical chart */}
      {history && history.length > 0 && <HistoryChart history={history} />}

      {/* Groups: one card per type, one table per subtype */}
      {groups.map(({ type, subtypes }) => {
        const typeGross = subtypes.flatMap(s => s.items).reduce((sum, i) => sum + (i.amount ?? 0), 0);
        const typeNet = subtypes.flatMap(s => s.items).reduce((sum, i) => sum + (i.balance ?? 0), 0);
        const typeLabel = TYPE_LABELS[type] ?? type;
        const isFixedIncome = type === 'FIXED_INCOME';

        return (
          <section key={type} className="bg-white rounded-lg shadow overflow-hidden">
            {/* Type header */}
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">{typeLabel}</h3>
              <div className="flex gap-6 text-sm text-gray-500">
                <span>Bruto: <span className="font-medium text-gray-800">{formatCurrency(typeGross)}</span></span>
                <span>Líquido: <span className="font-medium text-gray-800">{formatCurrency(typeNet)}</span></span>
              </div>
            </div>

            {/* One table per subtype */}
            {subtypes.map(({ subtype, items }) => {
              const subGross = items.reduce((sum, i) => sum + (i.amount ?? 0), 0);
              const subNet = items.reduce((sum, i) => sum + (i.balance ?? 0), 0);

              return (
                <div key={subtype}>
                  {/* Subtype header */}
                  <div className="px-6 py-2 border-b border-gray-100 flex items-center justify-between bg-white">
                    <span className="text-sm font-medium text-gray-600">{subtype}</span>
                    <div className="flex gap-6 text-sm text-gray-400">
                      <span>Bruto: <span className="font-medium text-gray-600">{formatCurrency(subGross)}</span></span>
                      <span>Líquido: <span className="font-medium text-gray-600">{formatCurrency(subNet)}</span></span>
                    </div>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full table-fixed divide-y divide-gray-100">
                      <thead className="bg-gray-50">
                        <tr>
                          {isFixedIncome ? (
                            <>
                              <Th width="35%">Nome</Th>
                              <Th width="35%">Emissor</Th>
                              <Th width="10%">Tipo de taxa</Th>
                              <Th width="10%">Vencimento</Th>
                              <Th width="5%" right>Bruto</Th>
                              <Th width="5%" right>Líquido</Th>
                            </>
                          ) : (
                            <>
                              <Th width="80%">Nome</Th>
                              <Th width="10%">Vencimento</Th>
                              <Th width="5%" right>Bruto</Th>
                              <Th width="5%" right>Líquido</Th>
                            </>
                          )}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {items.map(i => (
                          <tr key={i.id} className="hover:bg-gray-50">
                            <Td>{i.name}</Td>
                            {isFixedIncome && <Td>{i.issuer ?? '—'}</Td>}
                            {isFixedIncome && <Td>{i.rate_type ?? '—'}</Td>}
                            <Td>{formatDate(i.due_date)}</Td>
                            <Td right>{formatCurrency(i.amount)}</Td>
                            <Td right>{formatCurrency(i.balance)}</Td>
                          </tr>
                        ))}

                      </tbody>
                    </table>
                  </div>
                </div>
              );
            })}
          </section>
        );
      })}

      {list.length === 0 && (
        <div className="bg-white rounded-lg shadow p-12 text-center text-gray-500">
          Nenhum investimento encontrado.
        </div>
      )}
    </div>
  );
};

const SummaryCard: React.FC<{ label: string; value: number; highlight?: boolean }> = ({
  label,
  value,
  highlight,
}) => (
  <div className={`rounded-lg shadow p-4 ${highlight ? 'bg-primary-50' : 'bg-white'}`}>
    <p className="text-sm text-gray-500">{label}</p>
    <p className={`text-xl font-bold mt-1 ${highlight ? 'text-primary-700' : 'text-gray-900'}`}>
      {formatCurrency(value)}
    </p>
  </div>
);

const Th: React.FC<{ children: React.ReactNode; right?: boolean; width?: string }> = ({ children, right, width }) => (
  <th
    style={width ? { width } : undefined}
    className={`px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider ${right ? 'text-right' : 'text-left'}`}
  >
    {children}
  </th>
);

const Td: React.FC<{ children: React.ReactNode; right?: boolean }> = ({ children, right }) => (
  <td className={`px-6 py-4 text-sm text-gray-700 break-words ${right ? 'text-right whitespace-nowrap' : ''}`}>
    {children}
  </td>
);
