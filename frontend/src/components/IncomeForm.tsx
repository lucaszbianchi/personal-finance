import React, { useState, useEffect } from 'react';
import { useCreateIncomeSource, useUpdateIncomeSource, useIncomeMatchCount } from '@/hooks/useIncome';
import { useCategories } from '@/hooks/useCategories';
import { FREQUENCY_LABELS } from '@/constants/recurrences';
import type { IncomeSource } from '@/types';
import { AxiosError } from 'axios';

interface Props {
  initial?: IncomeSource;
  onClose: () => void;
}

const FREQUENCY_OPTIONS = [
  { value: 'monthly', label: 'Mensal' },
  { value: 'annual', label: 'Anual' },
  { value: 'weekly', label: 'Semanal' },
];


export const IncomeForm: React.FC<Props> = ({ initial, onClose }) => {
  const { data: categories } = useCategories();
  const create = useCreateIncomeSource();
  const update = useUpdateIncomeSource();

  const [form, setForm] = useState({
    description: initial?.description ?? '',
    amount: initial?.amount?.toString() ?? '',
    frequency: initial?.frequency ?? 'monthly',
    next_occurrence: initial?.next_occurrence ?? '',
    merchant_name: initial?.merchant_name ?? '',
    amount_min: initial?.amount_min?.toString() ?? '',
    amount_max: initial?.amount_max?.toString() ?? '',
    category_id: initial?.category_id ?? '',
  });

  const [debouncedMerchant, setDebouncedMerchant] = useState(form.merchant_name);
  const [debouncedMin, setDebouncedMin] = useState(form.amount_min);
  const [debouncedMax, setDebouncedMax] = useState(form.amount_max);

  useEffect(() => {
    const t = setTimeout(() => {
      setDebouncedMerchant(form.merchant_name);
      setDebouncedMin(form.amount_min);
      setDebouncedMax(form.amount_max);
    }, 400);
    return () => clearTimeout(t);
  }, [form.merchant_name, form.amount_min, form.amount_max]);

  const matchCountParams = {
    merchant_name: debouncedMerchant || undefined,
    amount_min: debouncedMin ? parseFloat(debouncedMin) : undefined,
    amount_max: debouncedMax ? parseFloat(debouncedMax) : undefined,
    next_occurrence: form.next_occurrence || undefined,
    frequency: form.frequency || undefined,
  };
  const { data: matchCountData } = useIncomeMatchCount(matchCountParams, Boolean(debouncedMerchant));

  const isEditing = Boolean(initial);
  const isPending = create.isPending || update.isPending;
  const [submitError, setSubmitError] = useState<string | null>(null);

  const nextDay = form.next_occurrence ? new Date(form.next_occurrence + 'T12:00:00').getDate() : null;
  const freqLabel = (FREQUENCY_LABELS[form.frequency] ?? form.frequency).toLowerCase();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    const data: Record<string, unknown> = {
      description: form.description,
      amount: parseFloat(form.amount) || 0,
      frequency: form.frequency,
      next_occurrence: form.next_occurrence || null,
      merchant_name: form.merchant_name || null,
      amount_min: form.amount_min ? parseFloat(form.amount_min) : null,
      amount_max: form.amount_max ? parseFloat(form.amount_max) : null,
      category_id: form.category_id || null,
    };

    try {
      if (isEditing && initial) {
        await update.mutateAsync({ id: initial.id, data });
      } else {
        await create.mutateAsync(data);
      }
      onClose();
    } catch (err) {
      const message =
        err instanceof AxiosError
          ? (err.response?.data?.error ?? err.message)
          : 'Erro ao salvar receita recorrente.';
      setSubmitError(String(message));
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-start justify-between p-6 pb-2">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              {isEditing ? 'Editar Receita Recorrente' : 'Nova Receita Recorrente'}
            </h2>
            <p className="text-sm text-gray-500 mt-0.5">Adicione uma receita recorrente</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors ml-4 mt-0.5"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 pt-4 space-y-4">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-600">Tipo de Transação:</span>
            <span className="text-xs font-semibold bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
              Receitas
            </span>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Descrição</label>
            <input
              name="description"
              value={form.description}
              onChange={handleChange}
              required
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Valor Esperado</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-gray-500">R$</span>
              <input
                name="amount"
                type="number"
                step="0.01"
                min="0"
                value={form.amount}
                onChange={handleChange}
                required
                className="w-full border border-gray-300 rounded pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Frequência</label>
            <select
              name="frequency"
              value={form.frequency}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {FREQUENCY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Próxima data esperada</label>
            <input
              name="next_occurrence"
              type="date"
              value={form.next_occurrence}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-400 mt-1">Quando é o próximo recebimento?</p>
          </div>

          {/* Matching rules */}
          <div className="border border-gray-200 rounded-lg p-4 bg-gray-50 space-y-3">
            <div>
              <p className="text-sm font-medium text-gray-700">Regras de correspondencia</p>
              <p className="text-xs text-gray-400 mt-0.5">
                Como o sistema identifica esta receita nas suas transações
              </p>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Transações com nome</label>
              <input
                name="merchant_name"
                value={form.merchant_name}
                onChange={handleChange}
                placeholder="ex: salario, freelance"
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex items-center gap-2">
              <label className="text-xs font-medium text-gray-600 whitespace-nowrap">de R$</label>
              <input
                name="amount_min"
                type="number"
                step="0.01"
                min="0"
                value={form.amount_min}
                onChange={handleChange}
                placeholder="0,00"
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <label className="text-xs font-medium text-gray-600 whitespace-nowrap">a R$</label>
              <input
                name="amount_max"
                type="number"
                step="0.01"
                min="0"
                value={form.amount_max}
                onChange={handleChange}
                placeholder="0,00"
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {nextDay !== null && (
              <p className="text-xs text-gray-500">
                por volta do Dia {nextDay} com frequencia {freqLabel}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Categoria</label>
            <select
              name="category_id"
              value={form.category_id}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Sem categoria</option>
              {(categories ?? []).map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.description_translated ?? cat.description}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center justify-between py-1">
            <span className="text-sm text-gray-700">Transações encontradas</span>
            <span className="text-sm font-semibold bg-green-100 text-green-700 px-2 py-0.5 rounded">
              {debouncedMerchant ? (matchCountData?.count ?? '-') : 0}
            </span>
          </div>

          {submitError && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
              {submitError}
            </p>
          )}

          <div className="flex flex-col items-center gap-2 pt-2">
            <button
              type="submit"
              disabled={isPending}
              className="w-full px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {isPending ? 'Salvando...' : isEditing ? 'Salvar' : 'Nova Receita Recorrente'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
            >
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
