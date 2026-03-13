import React, { useState } from 'react';
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react';
import { useMonthlySummary } from '@/hooks/useSummary';
import { MonthNavigator } from '@/components/MonthNavigator';
import { formatCurrency } from '@/utils/format';

const today = new Date();
const currentMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;

function DeltaBadge({ delta, invertColors = false }: { delta: number | null | undefined; invertColors?: boolean }) {
  if (delta == null) return null;
  const positive = delta >= 0;
  const isGood = invertColors ? !positive : positive;
  return (
    <span className={`flex items-center text-sm gap-1 ${isGood ? 'text-green-600' : 'text-red-600'}`}>
      {positive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
      {positive ? '+' : ''}{delta.toFixed(1)}%
    </span>
  );
}

export const Summary: React.FC = () => {
  const [month, setMonth] = useState(currentMonth);

  const { data, isLoading, error } = useMonthlySummary(month);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-600">Erro ao carregar resumo financeiro</p>
      </div>
    );
  }

  const current = data?.current;
  const comparison = data?.comparison;

  return (
    <div className="space-y-6">
      {/* Header with month navigator */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Resumo Financeiro</h2>
          <p className="text-gray-600">Análise detalhada do mês</p>
        </div>
        <MonthNavigator month={month} onChange={setMonth} maxMonth={currentMonth} />
      </div>

      {/* Income / Expenses / Balance */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-green-100 rounded-lg">
              <TrendingUp className="w-5 h-5 text-green-600" />
            </div>
            <h3 className="font-medium text-green-900">Receitas</h3>
          </div>
          <p className="text-2xl font-bold text-green-700">{formatCurrency(current?.income)}</p>
          <DeltaBadge delta={comparison?.income_delta_pct} />
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-red-100 rounded-lg">
              <TrendingDown className="w-5 h-5 text-red-600" />
            </div>
            <h3 className="font-medium text-red-900">Gastos</h3>
          </div>
          <p className="text-2xl font-bold text-red-700">{formatCurrency(current?.expenses)}</p>
          <DeltaBadge delta={comparison?.expenses_delta_pct} invertColors />
        </div>

        <div className={`border rounded-lg p-6 ${
          (current?.balance ?? 0) >= 0
            ? 'bg-blue-50 border-blue-200'
            : 'bg-orange-50 border-orange-200'
        }`}>
          <div className="flex items-center gap-3 mb-2">
            <div className={`p-2 rounded-lg ${(current?.balance ?? 0) >= 0 ? 'bg-blue-100' : 'bg-orange-100'}`}>
              <DollarSign className={`w-5 h-5 ${(current?.balance ?? 0) >= 0 ? 'text-blue-600' : 'text-orange-600'}`} />
            </div>
            <h3 className={`font-medium ${(current?.balance ?? 0) >= 0 ? 'text-blue-900' : 'text-orange-900'}`}>
              Saldo Líquido
            </h3>
          </div>
          <p className={`text-2xl font-bold ${(current?.balance ?? 0) >= 0 ? 'text-blue-700' : 'text-orange-700'}`}>
            {formatCurrency(current?.balance)}
          </p>
          <DeltaBadge delta={comparison?.balance_delta_pct} />
        </div>
      </div>
    </div>
  );
};
