import React from 'react';
import { useFinanceSummary } from '@/hooks/useSummary';
import { PieChart, BarChart, TrendingUp } from 'lucide-react';

export const Summary: React.FC = () => {
  const { data: summary, isLoading, error } = useFinanceSummary();

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-danger-50 border border-danger-200 rounded-md p-4">
        <p className="text-danger-600">Erro ao carregar resumo financeiro</p>
      </div>
    );
  }

  const summaryData = summary?.data?.data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Resumo Financeiro</h2>
        <p className="text-gray-600">Análise detalhada das suas finanças</p>
      </div>

      {/* Resumo geral */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-success-50 border border-success-200 rounded-lg p-6">
          <div className="flex items-center">
            <div className="p-2 bg-success-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-success-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-success-900">Receitas</h3>
              <p className="text-2xl font-bold text-success-700">
                {formatCurrency(summaryData?.total_income || 0)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-danger-50 border border-danger-200 rounded-lg p-6">
          <div className="flex items-center">
            <div className="p-2 bg-danger-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-danger-600 rotate-180" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-danger-900">Despesas</h3>
              <p className="text-2xl font-bold text-danger-700">
                {formatCurrency(summaryData?.total_expenses || 0)}
              </p>
            </div>
          </div>
        </div>

        <div className={`border rounded-lg p-6 ${
          summaryData?.net_balance && summaryData.net_balance >= 0
            ? 'bg-primary-50 border-primary-200'
            : 'bg-orange-50 border-orange-200'
        }`}>
          <div className="flex items-center">
            <div className={`p-2 rounded-lg ${
              summaryData?.net_balance && summaryData.net_balance >= 0
                ? 'bg-primary-100'
                : 'bg-orange-100'
            }`}>
              <BarChart className={`w-6 h-6 ${
                summaryData?.net_balance && summaryData.net_balance >= 0
                  ? 'text-primary-600'
                  : 'text-orange-600'
              }`} />
            </div>
            <div className="ml-4">
              <h3 className={`text-lg font-medium ${
                summaryData?.net_balance && summaryData.net_balance >= 0
                  ? 'text-primary-900'
                  : 'text-orange-900'
              }`}>
                Saldo Líquido
              </h3>
              <p className={`text-2xl font-bold ${
                summaryData?.net_balance && summaryData.net_balance >= 0
                  ? 'text-primary-700'
                  : 'text-orange-700'
              }`}>
                {formatCurrency(summaryData?.net_balance || 0)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Breakdown por categorias */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center mb-6">
          <PieChart className="w-6 h-6 text-gray-600 mr-2" />
          <h3 className="text-lg font-medium text-gray-900">
            Distribuição de Gastos por Categoria
          </h3>
        </div>

        {summaryData?.categories_breakdown?.length ? (
          <div className="space-y-4">
            {summaryData.categories_breakdown.map((item, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <div
                    className="w-4 h-4 rounded-full mr-3"
                    style={{
                      backgroundColor: `hsl(${(index * 137.5) % 360}, 70%, 60%)`
                    }}
                  />
                  <span className="font-medium text-gray-900">{item.category}</span>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-gray-900">
                    {formatCurrency(item.amount)}
                  </div>
                  <div className="text-sm text-gray-500">
                    {item.percentage.toFixed(1)}% do total
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500">
            <PieChart className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>Nenhum dado de categoria disponível para análise</p>
          </div>
        )}
      </div>

      {/* Período da análise */}
      {summaryData?.period && (
        <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
          <p className="text-sm text-primary-700">
            <strong>Período da análise:</strong> {summaryData.period}
          </p>
        </div>
      )}
    </div>
  );
};