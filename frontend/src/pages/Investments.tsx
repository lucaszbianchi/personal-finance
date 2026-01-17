import React from 'react';
import { TrendingUp, DollarSign } from 'lucide-react';

export const Investments: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Investimentos</h2>
          <p className="text-gray-600">Acompanhe o desempenho dos seus investimentos</p>
        </div>
      </div>

      {/* Em desenvolvimento */}
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <TrendingUp className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Módulo de Investimentos
        </h3>
        <p className="text-gray-500 mb-6">
          Esta funcionalidade está em desenvolvimento. Em breve você poderá acompanhar
          seus investimentos, rendimentos e performance da carteira.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-md mx-auto">
          <div className="text-center">
            <div className="bg-primary-50 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-2">
              <DollarSign className="w-6 h-6 text-primary-600" />
            </div>
            <p className="text-sm text-gray-600">Portfolio</p>
          </div>
          <div className="text-center">
            <div className="bg-success-50 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-2">
              <TrendingUp className="w-6 h-6 text-success-600" />
            </div>
            <p className="text-sm text-gray-600">Performance</p>
          </div>
          <div className="text-center">
            <div className="bg-purple-50 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-2">
              <TrendingUp className="w-6 h-6 text-purple-600" />
            </div>
            <p className="text-sm text-gray-600">Análises</p>
          </div>
        </div>
      </div>
    </div>
  );
};