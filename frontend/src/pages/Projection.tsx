import React, { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useProjection, useProjectionAssumptions } from '@/hooks/useProjection';
import { ProjectionChart } from '@/components/ProjectionChart';
import { formatCurrency } from '@/utils/format';
import { financeHistoryService, settingsService } from '@/services/api';

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-48">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
    </div>
  );
}

function shortMonthLabel(ym: string): string {
  const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
  const [year, m] = ym.split('-').map(Number);
  return `${months[m - 1]}/${String(year).slice(2)}`;
}

export const Projection: React.FC = () => {
  const queryClient = useQueryClient();
  const [rebuilding, setRebuilding] = useState(false);
  const [optionalTarget, setOptionalTarget] = useState<number>(0);
  const [savingTarget, setSavingTarget] = useState(false);
  const { data: projection, isLoading: loadingProjection } = useProjection(10);
  const { data: assumptions, isLoading: loadingAssumptions } = useProjectionAssumptions();

  const isLoading = loadingProjection || loadingAssumptions;

  // Sync local state with server value when assumptions load
  useEffect(() => {
    if (assumptions) {
      setOptionalTarget(assumptions.optional_expenses_target);
    }
  }, [assumptions?.optional_expenses_target]);

  async function handleRebuild() {
    setRebuilding(true);
    try {
      await financeHistoryService.rebuild();
      queryClient.invalidateQueries({ queryKey: ['projection'] });
    } finally {
      setRebuilding(false);
    }
  }

  async function handleSaveOptionalTarget() {
    setSavingTarget(true);
    try {
      await settingsService.updateOptionalExpensesTarget(optionalTarget);
      queryClient.invalidateQueries({ queryKey: ['projection'] });
    } finally {
      setSavingTarget(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Projecao Patrimonial</h1>
          <p className="text-sm text-gray-500 mt-1">Projecao de 12 meses baseada em receitas recorrentes e gastos fixos</p>
        </div>
        <button
          onClick={handleRebuild}
          disabled={rebuilding}
          className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {rebuilding ? 'Recalculando...' : 'Recalcular Historico'}
        </button>
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <>
          {/* Current net worth card */}
          {projection && (
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-sm text-gray-500">Patrimonio Atual</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">
                {formatCurrency(projection.current_net_worth)}
              </p>
            </div>
          )}

          {/* Projection chart */}
          {projection && (projection.history.length > 0 || projection.projection.length > 0) && (
            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="text-sm font-medium text-gray-500 mb-4">Historico e Projecao</h2>
              <ProjectionChart history={projection.history} projection={projection.projection} />
            </div>
          )}

          {/* Assumptions section */}
          {assumptions && (
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              {/* Income sources */}
              <div className="bg-white rounded-lg shadow p-4">
                <h2 className="text-sm font-semibold text-gray-700 mb-3">Receitas Recorrentes</h2>
                {assumptions.income_sources.length === 0 ? (
                  <p className="text-sm text-gray-400">Nenhuma receita mensal cadastrada</p>
                ) : (
                  <ul className="space-y-2">
                    {assumptions.income_sources.map((src, i) => (
                      <li key={i} className="flex justify-between text-sm">
                        <span className="text-gray-600 truncate">{src.description ?? '-'}</span>
                        <span className="font-medium text-green-700 ml-2 shrink-0">
                          {formatCurrency(src.amount)}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Fixed expenses */}
              <div className="bg-white rounded-lg shadow p-4">
                <h2 className="text-sm font-semibold text-gray-700 mb-3">Gastos Fixos</h2>
                {assumptions.fixed_expenses.length === 0 ? (
                  <p className="text-sm text-gray-400">Nenhum gasto fixo mensal cadastrado</p>
                ) : (
                  <ul className="space-y-2">
                    {assumptions.fixed_expenses.map((exp, i) => (
                      <li key={i} className="flex justify-between text-sm">
                        <span className="text-gray-600 truncate">{exp.description ?? '-'}</span>
                        <span className="font-medium text-red-600 ml-2 shrink-0">
                          {formatCurrency(exp.amount)}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Pending installments */}
              <div className="bg-white rounded-lg shadow p-4">
                <h2 className="text-sm font-semibold text-gray-700 mb-3">Parcelas Pendentes</h2>
                {assumptions.installments_by_month.length === 0 ? (
                  <p className="text-sm text-gray-400">Nenhuma parcela pendente</p>
                ) : (
                  <ul className="space-y-2">
                    {assumptions.installments_by_month.map((item, i) => (
                      <li key={i} className="flex justify-between text-sm">
                        <span className="text-gray-600">{shortMonthLabel(item.month)}</span>
                        <span className="font-medium text-orange-600 ml-2 shrink-0">
                          {formatCurrency(item.total)}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Average necessary expenses */}
              <div className="bg-white rounded-lg shadow p-4">
                <h2 className="text-sm font-semibold text-gray-700 mb-3">Media Gastos Necessarios</h2>
                <p className="text-xs text-gray-400 mb-3">
                  Media dos ultimos 6 meses (categorias necessarias - fixos - parcelas)
                </p>
                <p className="text-2xl font-bold text-purple-700">
                  {formatCurrency(assumptions.avg_necessary_expenses)}
                </p>
                <p className="text-xs text-gray-400 mt-1">por mes</p>
              </div>

              {/* Optional expenses target */}
              <div className="bg-white rounded-lg shadow p-4">
                <h2 className="text-sm font-semibold text-gray-700 mb-3">Meta Gastos Opcionais</h2>
                <p className="text-xs text-gray-400 mb-3">
                  Meta mensal para gastos opcionais na projecao
                </p>
                <div className="flex items-center gap-2 mb-1">
                  <input
                    type="number"
                    min="0"
                    step="50"
                    value={optionalTarget}
                    onChange={e => setOptionalTarget(Number(e.target.value))}
                    onBlur={handleSaveOptionalTarget}
                    disabled={savingTarget}
                    className="text-xl font-bold text-amber-600 w-32 border-b border-gray-300 bg-transparent focus:outline-none focus:border-amber-500 disabled:opacity-50"
                  />
                </div>
                <p className="text-xs text-gray-400 mt-1">por mes</p>
                <p className="text-xs text-gray-400 mt-2">
                  Media real ultimos 6 meses: {formatCurrency(assumptions.avg_optional_expenses_historical)}
                </p>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
