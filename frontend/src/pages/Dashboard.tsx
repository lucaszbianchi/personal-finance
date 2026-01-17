import React from 'react';
import { useFinanceSummary, useDashboardData } from '@/hooks/useSummary';
import { DollarSign, TrendingUp, TrendingDown, CreditCard } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string;
  change?: string;
  icon: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, change, icon, trend = 'neutral' }) => {
  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'text-success-600';
      case 'down':
        return 'text-danger-600';
      default:
        return 'text-gray-600';
    }
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4" />;
      case 'down':
        return <TrendingDown className="w-4 h-4" />;
      default:
        return null;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
          {change && (
            <div className={`flex items-center mt-1 ${getTrendColor()}`}>
              {getTrendIcon()}
              <span className="text-sm ml-1">{change}</span>
            </div>
          )}
        </div>
        <div className="p-3 bg-primary-50 rounded-full">
          {icon}
        </div>
      </div>
    </div>
  );
};

export const Dashboard: React.FC = () => {
  const { data: summary, isLoading: summaryLoading, error: summaryError } = useFinanceSummary();
  const { data: dashboard, isLoading: dashboardLoading } = useDashboardData();

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  if (summaryLoading || dashboardLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (summaryError) {
    return (
      <div className="bg-danger-50 border border-danger-200 rounded-md p-4">
        <p className="text-danger-600">Erro ao carregar dados do dashboard</p>
      </div>
    );
  }

  const summaryData = summary?.data;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Dashboard Financeiro</h2>
        <p className="text-gray-600">Visão geral das suas finanças pessoais</p>
      </div>

      {/* Métricas principais */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Receitas do Mês"
          value={formatCurrency(summaryData?.total_income || 0)}
          trend="up"
          icon={<TrendingUp className="w-6 h-6 text-primary-600" />}
        />
        <MetricCard
          title="Gastos do Mês"
          value={formatCurrency(summaryData?.total_expenses || 0)}
          trend="down"
          icon={<TrendingDown className="w-6 h-6 text-primary-600" />}
        />
        <MetricCard
          title="Saldo Líquido"
          value={formatCurrency(summaryData?.net_balance || 0)}
          trend={summaryData?.net_balance && summaryData.net_balance > 0 ? 'up' : 'down'}
          icon={<DollarSign className="w-6 h-6 text-primary-600" />}
        />
        <MetricCard
          title="Cartões de Crédito"
          value={formatCurrency(0)} // TODO: Implementar valor real
          icon={<CreditCard className="w-6 h-6 text-primary-600" />}
        />
      </div>

      {/* Gráficos e tabelas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Breakdown por categorias */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Gastos por Categoria
          </h3>
          {summaryData?.categories_breakdown?.length ? (
            <div className="space-y-3">
              {summaryData.categories_breakdown.map((item, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">{item.category}</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium">{item.percentage.toFixed(1)}%</span>
                    <span className="text-sm text-gray-500">
                      {formatCurrency(item.amount)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">
              Nenhum dado de categoria disponível
            </p>
          )}
        </div>

        {/* Transações recentes */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Transações Recentes
          </h3>
          <div className="space-y-3">
            <p className="text-gray-500 text-center py-8">
              Implementar lista de transações recentes
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};