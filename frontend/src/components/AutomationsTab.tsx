import React, { useState } from 'react';
import { Filter, Plus, Edit, Trash2, X, Search, Zap } from 'lucide-react';
import {
  useAutomations,
  useCreateAutomation,
  useUpdateAutomation,
  useDeleteAutomation,
  useToggleAutomation,
  usePreviewAutomation,
  useApplyAutomation,
} from '@/hooks/useAutomations';
import { useCategories } from '@/hooks/useCategories';
import { formatCurrency } from '@/utils/format';
import type {
  AutomationRule,
  AutomationCondition,
  AutomationConditionField,
  AutomationConditionOperator,
  AutomationPreviewTransaction,
} from '@/types';

const FIELD_LABELS: Record<AutomationConditionField, string> = {
  description: 'Descrição',
  category: 'Categoria',
  amount: 'Valor',
};

const FIELD_OPERATORS: Record<AutomationConditionField, { value: AutomationConditionOperator; label: string }[]> = {
  description: [
    { value: 'equals', label: 'é exatamente' },
    { value: 'contains', label: 'contém' },
    { value: 'starts_with', label: 'começa com' },
    { value: 'ends_with', label: 'termina com' },
  ],
  category: [
    { value: 'equals', label: 'é' },
  ],
  amount: [
    { value: 'equals', label: 'igual a' },
    { value: 'gt', label: 'maior que' },
    { value: 'lt', label: 'menor que' },
  ],
};

const BLANK_CONDITION: AutomationCondition = {
  field: 'description',
  operator: 'equals',
  value: '',
};

interface FormState {
  name: string;
  conditions: AutomationCondition[];
  actionCategory: string;
  actionExclude: boolean;
  actionDescription: string;
}

const BLANK_FORM: FormState = {
  name: '',
  conditions: [{ ...BLANK_CONDITION }],
  actionCategory: '',
  actionExclude: false,
  actionDescription: '',
};

function ruleToForm(rule: AutomationRule): FormState {
  const cat = rule.actions.find(a => a.type === 'set_category');
  const excl = rule.actions.find(a => a.type === 'exclude');
  const desc = rule.actions.find(a => a.type === 'set_description');
  return {
    name: rule.name ?? '',
    conditions: rule.conditions.length > 0 ? rule.conditions : [{ ...BLANK_CONDITION }],
    actionCategory: cat?.value ?? '',
    actionExclude: !!excl,
    actionDescription: desc?.value ?? '',
  };
}

function formToActions(form: FormState) {
  const actions = [];
  if (form.actionCategory) actions.push({ type: 'set_category' as const, value: form.actionCategory });
  if (form.actionExclude) actions.push({ type: 'exclude' as const });
  if (form.actionDescription.trim()) actions.push({ type: 'set_description' as const, value: form.actionDescription.trim() });
  return actions;
}

export const AutomationsTab: React.FC = () => {
  const { data: rules = [] } = useAutomations();
  const { data: categories = [] } = useCategories();
  const createAutomation = useCreateAutomation();
  const updateAutomation = useUpdateAutomation();
  const deleteAutomation = useDeleteAutomation();
  const toggleAutomation = useToggleAutomation();
  const previewMutation = usePreviewAutomation();
  const applyMutation = useApplyAutomation();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<AutomationRule | null>(null);
  const [form, setForm] = useState<FormState>(BLANK_FORM);
  const [formError, setFormError] = useState('');
  const [previewResults, setPreviewResults] = useState<AutomationPreviewTransaction[] | null>(null);
  const [applyFeedback, setApplyFeedback] = useState<Record<number, string>>({});

  const openCreate = () => {
    setEditingRule(null);
    setForm(BLANK_FORM);
    setFormError('');
    setPreviewResults(null);
    setIsModalOpen(true);
  };

  const openEdit = (rule: AutomationRule) => {
    setEditingRule(rule);
    setForm(ruleToForm(rule));
    setFormError('');
    setPreviewResults(null);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingRule(null);
    setPreviewResults(null);
  };

  const updateCondition = (index: number, patch: Partial<AutomationCondition>) => {
    setForm(prev => ({
      ...prev,
      conditions: prev.conditions.map((c, i) => {
        if (i !== index) return c;
        const updated = { ...c, ...patch };
        // Reset operator when field changes to avoid invalid combinations
        if (patch.field && patch.field !== c.field) {
          const validOps = FIELD_OPERATORS[patch.field];
          if (!validOps.find(o => o.value === updated.operator)) {
            updated.operator = validOps[0].value;
          }
          updated.value = '';
        }
        return updated;
      }),
    }));
    setPreviewResults(null);
  };

  const addCondition = () => {
    setForm(prev => ({ ...prev, conditions: [...prev.conditions, { ...BLANK_CONDITION }] }));
    setPreviewResults(null);
  };

  const removeCondition = (index: number) => {
    setForm(prev => ({
      ...prev,
      conditions: prev.conditions.filter((_, i) => i !== index),
    }));
    setPreviewResults(null);
  };

  const handlePreview = async () => {
    try {
      const results = await previewMutation.mutateAsync(form.conditions);
      setPreviewResults(results);
    } catch {
      setPreviewResults([]);
    }
  };

  const handleSave = async () => {
    setFormError('');
    const actions = formToActions(form);
    if (actions.length === 0) {
      setFormError('Selecione ao menos uma ação.');
      return;
    }
    const payload = {
      name: form.name.trim() || undefined,
      conditions: form.conditions,
      actions,
    };
    try {
      if (editingRule) {
        await updateAutomation.mutateAsync({ id: editingRule.id, data: payload });
      } else {
        await createAutomation.mutateAsync(payload);
      }
      closeModal();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setFormError(msg);
    }
  };

  const handleApplyFromModal = async () => {
    if (!editingRule) return;
    try {
      const result = await applyMutation.mutateAsync(editingRule.id);
      setApplyFeedback(prev => ({
        ...prev,
        [editingRule.id]: `${result.applied} transação(ões) atualizada(s).`,
      }));
      closeModal();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setFormError(msg);
    }
  };

  const handleApplyFromList = async (rule: AutomationRule) => {
    try {
      const result = await applyMutation.mutateAsync(rule.id);
      setApplyFeedback(prev => ({
        ...prev,
        [rule.id]: `${result.applied} transação(ões) atualizada(s).`,
      }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setApplyFeedback(prev => ({ ...prev, [rule.id]: `Erro: ${msg}` }));
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Excluir esta automação?')) return;
    await deleteAutomation.mutateAsync(id);
  };

  const handleToggle = (rule: AutomationRule) => {
    toggleAutomation.mutate({ id: rule.id, enabled: !rule.enabled });
  };

  return (
    <div className="space-y-6">
      {rules.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 flex flex-col items-center text-center">
          <Filter className="w-12 h-12 text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhuma automação ainda</h3>
          <p className="text-gray-500 mb-6">
            Crie regras para categorizar transações automaticamente.
          </p>
          <button
            onClick={openCreate}
            className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Criar Automação</span>
          </button>
        </div>
      ) : (
        <>
          <div className="flex justify-end">
            <button
              onClick={openCreate}
              className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 flex items-center space-x-2"
            >
              <Plus className="w-4 h-4" />
              <span>Nova Automação</span>
            </button>
          </div>
          <div className="space-y-3">
            {rules.map(rule => (
              <div key={rule.id} className="bg-white rounded-lg shadow px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={rule.enabled}
                        onChange={() => handleToggle(rule)}
                      />
                      <div className="w-10 h-6 bg-gray-200 peer-checked:bg-primary-600 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
                    </label>
                    <span className="text-sm font-medium text-gray-900">
                      {rule.name ?? `Regra #${rule.id}`}
                    </span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={() => handleApplyFromList(rule)}
                      disabled={applyMutation.isPending}
                      className="text-secondary-600 hover:text-secondary-800 flex items-center space-x-1 disabled:opacity-50"
                      title="Aplicar às transações existentes"
                    >
                      <Zap className="w-4 h-4" />
                      <span className="text-sm">Aplicar</span>
                    </button>
                    <button
                      onClick={() => openEdit(rule)}
                      className="text-primary-600 hover:text-primary-800 flex items-center space-x-1"
                    >
                      <Edit className="w-4 h-4" />
                      <span className="text-sm">Editar</span>
                    </button>
                    <button
                      onClick={() => handleDelete(rule.id)}
                      className="text-danger-600 hover:text-danger-800 flex items-center space-x-1"
                    >
                      <Trash2 className="w-4 h-4" />
                      <span className="text-sm">Excluir</span>
                    </button>
                  </div>
                </div>
                {applyFeedback[rule.id] && (
                  <p className="mt-2 text-xs text-secondary-700 bg-secondary-50 rounded px-3 py-1">
                    {applyFeedback[rule.id]}
                  </p>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      {isModalOpen && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-6 border w-full max-w-xl shadow-lg rounded-md bg-white">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-lg font-medium text-gray-900">
                {editingRule ? 'Editar Regra' : 'Nova Automação'}
              </h3>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-5">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome da Regra
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={e => setForm(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 text-sm"
                  placeholder="Nome opcional"
                />
              </div>

              {/* Conditions */}
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Condições (SE)</p>
                <div className="space-y-2">
                  {form.conditions.map((cond, idx) => (
                    <div key={idx} className="flex items-center space-x-2">
                      <select
                        value={cond.field}
                        onChange={e =>
                          updateCondition(idx, { field: e.target.value as AutomationConditionField })
                        }
                        className="border border-gray-300 rounded-md px-2 py-1.5 text-sm focus:ring-primary-500 focus:border-primary-500"
                      >
                        {(Object.keys(FIELD_LABELS) as AutomationConditionField[]).map(f => (
                          <option key={f} value={f}>{FIELD_LABELS[f]}</option>
                        ))}
                      </select>
                      <select
                        value={cond.operator}
                        onChange={e =>
                          updateCondition(idx, { operator: e.target.value as AutomationConditionOperator })
                        }
                        className="border border-gray-300 rounded-md px-2 py-1.5 text-sm focus:ring-primary-500 focus:border-primary-500"
                      >
                        {FIELD_OPERATORS[cond.field].map(({ value: val, label }) => (
                          <option key={val} value={val}>{label}</option>
                        ))}
                      </select>
                      {cond.field === 'category' ? (
                        <select
                          value={cond.value}
                          onChange={e => updateCondition(idx, { value: e.target.value })}
                          className="flex-1 border border-gray-300 rounded-md px-2 py-1.5 text-sm focus:ring-primary-500 focus:border-primary-500"
                        >
                          <option value="">— Selecione —</option>
                          {categories.map(cat => (
                            <option key={cat.id} value={cat.id}>
                              {cat.description_translated ?? cat.description}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <input
                          type={cond.field === 'amount' ? 'number' : 'text'}
                          value={cond.value}
                          onChange={e => updateCondition(idx, { value: e.target.value })}
                          className="flex-1 border border-gray-300 rounded-md px-2 py-1.5 text-sm focus:ring-primary-500 focus:border-primary-500"
                          placeholder={cond.field === 'amount' ? 'Ex: 100.00' : 'Valor'}
                        />
                      )}
                      {form.conditions.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeCondition(idx)}
                          className="text-gray-400 hover:text-gray-600"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={addCondition}
                  className="mt-2 text-sm text-primary-600 hover:text-primary-800"
                >
                  + Adicionar Condição
                </button>
              </div>

              {/* Actions */}
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Ações (ENTÃO)</p>
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">Definir Categoria</label>
                    <select
                      value={form.actionCategory}
                      onChange={e => setForm(prev => ({ ...prev, actionCategory: e.target.value }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="">— Nenhuma —</option>
                      {categories.map(cat => (
                        <option key={cat.id} value={cat.id}>
                          {cat.description_translated ?? cat.description}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      id="actionExclude"
                      type="checkbox"
                      checked={form.actionExclude}
                      onChange={e => setForm(prev => ({ ...prev, actionExclude: e.target.checked }))}
                      className="h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                    />
                    <label htmlFor="actionExclude" className="text-sm text-gray-700">
                      Excluir das análises
                    </label>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">Alterar Descrição</label>
                    <input
                      type="text"
                      value={form.actionDescription}
                      onChange={e => setForm(prev => ({ ...prev, actionDescription: e.target.value }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-primary-500 focus:border-primary-500"
                      placeholder="Nova descrição (opcional)"
                    />
                  </div>
                </div>
              </div>

              {/* Preview section */}
              <div className="border-t pt-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium text-gray-700">Transações correspondentes</p>
                  <button
                    type="button"
                    onClick={handlePreview}
                    disabled={previewMutation.isPending}
                    className="flex items-center space-x-1 text-sm text-primary-600 hover:text-primary-800 disabled:opacity-50"
                  >
                    <Search className="w-3.5 h-3.5" />
                    <span>{previewMutation.isPending ? 'Buscando...' : 'Buscar transações'}</span>
                  </button>
                </div>
                {previewResults !== null && (
                  previewResults.length === 0 ? (
                    <p className="text-sm text-gray-500 py-2">Nenhuma transação encontrada.</p>
                  ) : (
                    <div>
                      <p className="text-xs text-gray-500 mb-2">
                        {previewResults.length} transação(ões) encontrada(s)
                        {previewResults.length === 100 ? ' (limite de 100)' : ''}
                      </p>
                      <div className="max-h-44 overflow-y-auto space-y-1 rounded border border-gray-100 p-1">
                        {previewResults.slice(0, 15).map(t => (
                          <div
                            key={`${t.type}-${t.id}`}
                            className="flex items-center justify-between text-xs px-2 py-1.5 bg-gray-50 rounded"
                          >
                            <span className={`text-xs font-medium px-1.5 py-0.5 rounded mr-2 ${
                              t.type === 'bank'
                                ? 'bg-blue-100 text-blue-700'
                                : 'bg-purple-100 text-purple-700'
                            }`}>
                              {t.type === 'bank' ? 'Banco' : 'Crédito'}
                            </span>
                            <span className="text-gray-700 truncate flex-1">{t.description}</span>
                            <span className="text-gray-400 ml-2 shrink-0">{t.date?.slice(0, 10)}</span>
                            <span className={`ml-3 font-medium shrink-0 ${
                              t.amount < 0 ? 'text-danger-600' : 'text-success-600'
                            }`}>
                              {formatCurrency(t.amount)}
                            </span>
                          </div>
                        ))}
                        {previewResults.length > 15 && (
                          <p className="text-xs text-gray-400 text-center py-1">
                            e mais {previewResults.length - 15}...
                          </p>
                        )}
                      </div>
                    </div>
                  )
                )}
              </div>

              {formError && (
                <p className="text-sm text-danger-600 bg-danger-50 rounded px-3 py-2">{formError}</p>
              )}
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                type="button"
                onClick={closeModal}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancelar
              </button>
              {editingRule && previewResults && previewResults.length > 0 && (
                <button
                  type="button"
                  onClick={handleApplyFromModal}
                  disabled={applyMutation.isPending}
                  className="px-4 py-2 bg-secondary-600 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-secondary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1"
                >
                  <Zap className="w-4 h-4" />
                  <span>
                    {applyMutation.isPending
                      ? 'Aplicando...'
                      : `Aplicar às existentes (${previewResults.length})`}
                  </span>
                </button>
              )}
              <button
                type="button"
                onClick={handleSave}
                disabled={createAutomation.isPending || updateAutomation.isPending}
                className="px-4 py-2 bg-primary-600 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {(createAutomation.isPending || updateAutomation.isPending) ? 'Salvando...' : 'Salvar Regra'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
