import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface KpiCardProps {
  title: string;
  value: string;
  delta?: number | null; // percentage delta vs previous period
  icon: React.ReactNode;
  subtitle?: string;
}

export const KpiCard: React.FC<KpiCardProps> = ({ title, value, delta, icon, subtitle }) => {
  const hasDelta = delta != null;
  const isPositive = hasDelta && delta >= 0;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-600 truncate">{title}</p>
          <p className="text-2xl font-semibold text-gray-900 mt-1">{value}</p>
          {hasDelta && (
            <div className={`flex items-center mt-1 ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
              {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              <span className="text-sm ml-1">{isPositive ? '+' : ''}{delta.toFixed(1)}%</span>
            </div>
          )}
          {subtitle && !hasDelta && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        <div className="p-3 bg-primary-50 rounded-full ml-4 flex-shrink-0">
          {icon}
        </div>
      </div>
    </div>
  );
};
