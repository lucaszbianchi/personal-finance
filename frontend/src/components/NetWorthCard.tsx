import React from 'react';
import { Landmark } from 'lucide-react';
import { formatCurrency } from '@/utils/format';
import type { NetWorth } from '@/types';

interface Props {
  data: NetWorth;
}

export const NetWorthCard: React.FC<Props> = ({ data }) => {
  const { checking_balance, investments_total, net_worth } = data;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center gap-2 mb-4">
        <Landmark className="w-5 h-5 text-primary-600" />
        <h3 className="text-lg font-medium text-gray-900">Patrimônio</h3>
      </div>

      <p className="text-3xl font-bold text-gray-900 mb-4">
        {formatCurrency(net_worth)}
      </p>

      <div className="space-y-2">
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-500 flex items-center gap-1">
            <span className="inline-block w-2 h-2 rounded-full bg-blue-500" />
            Conta corrente
          </span>
          <span className="font-medium text-gray-700">
            {formatCurrency(checking_balance)}
          </span>
        </div>
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-500 flex items-center gap-1">
            <span className="inline-block w-2 h-2 rounded-full bg-green-500" />
            Investimentos
          </span>
          <span className="font-medium text-gray-700">
            {formatCurrency(investments_total)}
          </span>
        </div>
      </div>
    </div>
  );
};
