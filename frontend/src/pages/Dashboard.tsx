import React from 'react';
import { DollarSign, TrendingUp, TrendingDown } from 'lucide-react';
import { useDashboardData } from '@/hooks/useDashboardData';
import { KpiCard } from '@/components/KpiCard';
import { MonthlyBarChart } from '@/components/MonthlyBarChart';
import { CategoryPieChart } from '@/components/CategoryPieChart';
import { formatCurrency } from '@/utils/format';

export const Dashboard: React.FC = () => {
  const { data, isLoading, error } = useDashboardData();

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
        <p className="text-red-600">Erro ao carregar dados do dashboard</p>
      </div>
    );
  }

  const cm = data?.current_month;
  const history = data?.history ?? [];
  const categoryBreakdown = data?.category_breakdown ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Dashboard Financeiro</h2>
        <p className="text-gray-600">Visão geral das suas finanças pessoais</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <KpiCard
          title="Receitas do Mês"
          value={formatCurrency(cm?.income)}
          icon={<TrendingUp className="w-6 h-6 text-primary-600" />}
        />
        <KpiCard
          title="Gastos do Mês"
          value={formatCurrency(cm?.expenses)}
          icon={<TrendingDown className="w-6 h-6 text-primary-600" />}
        />
        <KpiCard
          title="Saldo Líquido"
          value={formatCurrency(cm?.balance)}
          icon={<DollarSign className="w-6 h-6 text-primary-600" />}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Histórico 12 Meses — Receitas vs Gastos
          </h3>
          {history.length > 0 ? (
            <MonthlyBarChart data={history} />
          ) : (
            <p className="text-gray-500 text-center py-8 text-sm">
              Nenhum histórico disponível
            </p>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Distribuição por Categoria
          </h3>
          {categoryBreakdown.length > 0 ? (
            <CategoryPieChart data={categoryBreakdown} />
          ) : (
            <p className="text-gray-500 text-center py-8 text-sm">
              Nenhum dado de categoria disponível
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
