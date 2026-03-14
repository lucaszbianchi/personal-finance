import React from 'react';
import { Target } from 'lucide-react';
import { formatCurrency } from '@/utils/format';
import type { PartialResult } from '@/types';

interface Props {
  data: PartialResult;
}

function progressColor(pct: number): string {
  if (pct >= 80) return 'bg-green-500';
  if (pct >= 50) return 'bg-yellow-400';
  return 'bg-red-500';
}

export const PartialResultCard: React.FC<Props> = ({ data }) => {
  const { income_so_far, expenses_so_far, partial_balance, monthly_balance_goal, goal_pct } = data;
  const clampedPct = goal_pct != null ? Math.min(Math.max(goal_pct, 0), 100) : null;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center gap-2 mb-4">
        <Target className="w-5 h-5 text-primary-600" />
        <h3 className="text-lg font-medium text-gray-900">Resultado Parcial</h3>
      </div>

      <p className="text-3xl font-bold text-gray-900 mb-4">
        {formatCurrency(partial_balance)}
      </p>

      <div className="space-y-2 mb-4">
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-500">Receitas até agora</span>
          <span className="font-medium text-green-600">{formatCurrency(income_so_far)}</span>
        </div>
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-500">Gastos até agora</span>
          <span className="font-medium text-red-500">{formatCurrency(expenses_so_far)}</span>
        </div>
      </div>

      {monthly_balance_goal != null && clampedPct != null && (
        <div>
          <div className="flex justify-between items-center text-xs text-gray-500 mb-1">
            <span>Meta de saldo: {formatCurrency(monthly_balance_goal)}</span>
            <span className="font-medium">{goal_pct!.toFixed(1)}%</span>
          </div>
          <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-2 rounded-full transition-all ${progressColor(clampedPct)}`}
              style={{ width: `${clampedPct}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
};
