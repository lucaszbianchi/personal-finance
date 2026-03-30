import React, { useState, useEffect, useMemo } from 'react';
import { useCategories } from '@/hooks/useCategories';
import { useCategoryLabel, useCategoryLabelByName } from '@/hooks/useCategoryLabel';
import { useCategoryFilter } from '@/hooks/useCategoryFilter';
import { TransactionForm } from '@/components/TransactionForm';
import { useDeleteBankTransaction, useDeleteCreditTransaction, useToggleExcluded } from '@/hooks/useTransactions';
import { CreditCard, Landmark, Filter, X, ChevronDown, Plus, Tag, MoreVertical, Trash2, AlertTriangle } from 'lucide-react';
import type { Category } from '@/types';

interface Transaction {
  id: string;
  date: string;
  description: string;
  amount: number;
  category?: string;
  operation_type?: string;
  status?: string;
  type?: string;
  payment_data?: any;
  excluded?: number;
  account_alias?: string;
}

type TransactionType = 'bank' | 'credit';

export const Transactions: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TransactionType>('bank');
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [filteredTransactions, setFilteredTransactions] = useState<Transaction[]>([]);
  const [availablePeriods, setAvailablePeriods] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filtros (preservados entre tabs)
  const [selectedPeriod, setSelectedPeriod] = useState<string>('__all__');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [showFilters, setShowFilters] = useState(false);

  // Estado para formulário de criação
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Estado para exclusão de análises
  const [showExcluded, setShowExcluded] = useState(false);
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [menuPosition, setMenuPosition] = useState<{ top: number; right: number } | null>(null);

  // Estado para confirmação de delete
  const [deleteTarget, setDeleteTarget] = useState<Transaction | null>(null);
  const deleteBankTransaction = useDeleteBankTransaction();
  const deleteCreditTransaction = useDeleteCreditTransaction();
  const toggleExcluded = useToggleExcluded();
  const isDeleting = deleteBankTransaction.isPending || deleteCreditTransaction.isPending;

  // Estado para multi-select e bulk category
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [showBulkCategoryModal, setShowBulkCategoryModal] = useState(false);
  const [bulkCategoryId, setBulkCategoryId] = useState<string>('');

  const { data: categories } = useCategories();
  const { getCategoryLabel } = useCategoryLabel();
  const categoriesList: Category[] = useMemo(() => categories || [], [categories]);

  const {
    parentFilter: bulkParentFilter,
    setParentFilter: setBulkParentFilter,
    catByDescription,
    uniqueParents: bulkUniqueParents,
    filteredCategories: bulkFilteredCategories,
    resetFilter: resetBulkParentFilter,
  } = useCategoryFilter(categoriesList);

  const getCategoryLabelByName = useCategoryLabelByName(catByDescription);

  // Limpar seleção ao trocar de aba
  useEffect(() => {
    setSelectedIds([]);
  }, [activeTab]);

  // Carregar períodos disponíveis apenas uma vez no mount
  useEffect(() => {
    const loadAvailablePeriods = async () => {
      try {
        const response = await fetch('/api/transactions/bank');
        if (!response.ok) throw new Error('Erro ao carregar períodos');
        const data: Transaction[] = await response.json();

        const periods = new Set<string>();
        data.forEach(t => {
          const date = t.date.split('\n')[0] || t.date.split('T')[0];
          const period = date.slice(0, 7); // YYYY-MM
          periods.add(period);
        });
        setAvailablePeriods(Array.from(periods).sort().reverse());
      } catch (err) {
        console.error('Erro ao carregar períodos:', err);
      }
    };

    loadAvailablePeriods();
  }, []);

  // Buscar transações quando a aba muda ou filtros mudam
  useEffect(() => {
    const fetchTransactions = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();

        if (selectedPeriod && selectedPeriod !== '__all__') {
          const [year, month] = selectedPeriod.split('-');
          const startDate = `${year}-${month}-01`;
          const lastDay = new Date(parseInt(year), parseInt(month), 0).getDate();
          const endDate = `${year}-${month}-${String(lastDay).padStart(2, '0')}`;
          params.append('start_date', startDate);
          params.append('end_date', endDate);
        }

        if (selectedCategory && categoriesList.length > 0) {
          const category = categoriesList.find(cat => cat.description === selectedCategory);
          if (category) {
            params.append('category_id', category.id);
          }
        }

        const queryString = params.toString();
        const endpoint = `/api/transactions/${activeTab}${queryString ? `?${queryString}` : ''}`;

        const response = await fetch(endpoint);
        if (!response.ok) throw new Error('Erro ao carregar transações');
        const data = await response.json();
        setTransactions(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erro desconhecido');
      } finally {
        setIsLoading(false);
      }
    };

    fetchTransactions();
  }, [activeTab, selectedPeriod, selectedCategory, refreshTrigger]);

  // Aplicar filtro de texto (busca) e exclusão no frontend
  useEffect(() => {
    let filtered = [...transactions];

    if (!showExcluded) {
      filtered = filtered.filter(t => !t.excluded);
    }

    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(t =>
        t.description.toLowerCase().includes(search)
      );
    }

    setFilteredTransactions(filtered);
  }, [transactions, searchTerm, showExcluded]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatDate = (dateStr: string) => {
    const parts = dateStr.split('\n');
    const datePart = parts[0].trim();
    const timePart = parts[1]?.trim() ?? '';
    const [year, month, day] = datePart.split('-');
    if (timePart) {
      const [hours, minutes] = timePart.split(':');
      return `${day}/${month}/${year} ${hours}:${minutes}`;
    }
    return `${day}/${month}/${year}`;
  };

  const getAmountColor = (amount: number) => {
    if (activeTab === 'bank') {
      return amount > 0 ? 'text-success-600' : 'text-danger-600';
    } else {
      return amount > 0 ? 'text-danger-600' : 'text-success-600';
    }
  };

  const clearFilters = () => {
    setSelectedPeriod('__all__');
    setSelectedCategory('');
    setSearchTerm('');
  };

  const hasActiveFilters = selectedPeriod !== '__all__' || selectedCategory !== '' || searchTerm !== '';

  const handleTransactionCreated = () => {
    setShowCreateForm(false);
    setRefreshTrigger(prev => prev + 1);
  };

  const handleSelectAll = () => {
    if (selectedIds.length === filteredTransactions.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filteredTransactions.map(t => t.id));
    }
  };

  const handleSelectTransaction = (id: string) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(sid => sid !== id) : [...prev, id]
    );
  };

  const handleToggleExcluded = async (transaction: Transaction) => {
    await toggleExcluded.mutateAsync({
      type: activeTab,
      id: transaction.id,
      excluded: !transaction.excluded,
    });
    setRefreshTrigger(prev => prev + 1);
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      if (activeTab === 'bank') {
        await deleteBankTransaction.mutateAsync(deleteTarget.id);
      } else {
        await deleteCreditTransaction.mutateAsync(deleteTarget.id);
      }
      setDeleteTarget(null);
      setRefreshTrigger(prev => prev + 1);
    } catch {
      alert('Erro ao deletar transação. Tente novamente.');
    }
  };

  const handleBulkCategorySave = async () => {
    try {
      const response = await fetch(`/api/transactions/${activeTab}/bulk-category`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transaction_ids: selectedIds,
          category_id: bulkCategoryId || null,
        }),
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Erro ao atualizar categorias');
      }
      setShowBulkCategoryModal(false);
      setBulkCategoryId('');
      resetBulkParentFilter();
      setSelectedIds([]);
      setRefreshTrigger(prev => prev + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao atualizar categorias');
    }
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
        <p className="text-danger-600">Erro ao carregar transações: {error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Transações</h2>
          <p className="text-gray-600">Gerencie suas transações bancárias e de cartão</p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Nova Transação</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('bank')}
            className={`${
              activeTab === 'bank'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
          >
            <Landmark className="w-4 h-4" />
            <span>Transações Bancárias</span>
          </button>
          <button
            onClick={() => setActiveTab('credit')}
            className={`${
              activeTab === 'credit'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
          >
            <CreditCard className="w-4 h-4" />
            <span>Transações de Crédito</span>
          </button>
        </nav>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center space-x-2 text-gray-700 hover:text-gray-900"
          >
            <Filter className="w-4 h-4" />
            <span className="font-medium">Filtros</span>
            <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </button>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="flex items-center space-x-1 text-sm text-primary-600 hover:text-primary-700"
            >
              <X className="w-4 h-4" />
              <span>Limpar filtros</span>
            </button>
          )}
        </div>

        {showFilters && (
          <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Filtro de Período */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Período
              </label>
              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="__all__">Todos os períodos</option>
                {availablePeriods.map(period => (
                  <option key={period} value={period}>
                    {period}
                  </option>
                ))}
              </select>
            </div>

            {/* Filtro de Categoria */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Categoria
              </label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Todas as categorias</option>
                {categoriesList.filter(cat => cat.transaction_count > 0).map(cat => (
                  <option key={cat.id} value={cat.description}>
                    {getCategoryLabel(cat)}
                  </option>
                ))}
              </select>
            </div>

            {/* Busca por texto */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Buscar descrição
              </label>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Digite para buscar..."
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>
          <div className="mt-4">
            <button
              onClick={() => setShowExcluded(prev => !prev)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium border transition-colors ${
                showExcluded
                  ? 'bg-gray-700 text-white border-gray-700'
                  : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
              }`}
            >
              {showExcluded ? 'Ocultar excluídas' : 'Mostrar excluídas'}
            </button>
          </div>
          </>
        )}

        {/* Resumo dos resultados e botão de bulk */}
        <div className="mt-4 pt-4 border-t border-gray-200 flex items-center justify-between">
          <p className="text-sm text-gray-600">
            Mostrando <span className="font-semibold">{filteredTransactions.length}</span> de{' '}
            <span className="font-semibold">{transactions.length}</span> transações
          </p>
          {selectedIds.length > 0 && (
            <button
              onClick={() => setShowBulkCategoryModal(true)}
              className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 flex items-center space-x-2"
            >
              <Tag className="w-4 h-4" />
              <span>Atualizar {selectedIds.length} {selectedIds.length === 1 ? 'transação' : 'transações'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Tabela de transações */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 table-fixed">
            <thead className="bg-gray-50">
              <tr>
                <th className="w-px px-4 py-3">
                  <input
                    type="checkbox"
                    checked={filteredTransactions.length > 0 && selectedIds.length === filteredTransactions.length}
                    ref={(el) => {
                      if (el) {
                        el.indeterminate = selectedIds.length > 0 && selectedIds.length < filteredTransactions.length;
                      }
                    }}
                    onChange={handleSelectAll}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                </th>
                <th className="w-[12%] px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Data
                </th>
                <th className="w-[50%] px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Descrição
                </th>
                <th className="w-[20%] px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Categoria
                </th>
                <th className="w-[13%] px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Valor
                </th>
                <th className="w-[7%] px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredTransactions.length > 0 ? (
                filteredTransactions.map((transaction) => (
                  <tr
                    key={transaction.id}
                    className={`hover:bg-gray-50 transition-colors ${transaction.excluded ? 'opacity-40' : ''}`}
                  >
                    <td className="px-4 py-4">
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(transaction.id)}
                        onChange={() => handleSelectTransaction(transaction.id)}
                        className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(transaction.date)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <div className="max-w-md" title={transaction.description}>
                        {transaction.description}
                      </div>
                      {transaction.account_alias && (
                        <span className="inline-block mt-0.5 text-[10px] bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded-full">
                          {transaction.account_alias}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        {transaction.category
                          ? getCategoryLabelByName(transaction.category)
                          : 'Sem categoria'}
                      </span>
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm font-semibold ${getAmountColor(transaction.amount)}`}>
                      {formatCurrency(transaction.amount)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                      <button
                        onClick={(e) => {
                          if (openMenuId === transaction.id) {
                            setOpenMenuId(null);
                            setMenuPosition(null);
                          } else {
                            const rect = e.currentTarget.getBoundingClientRect();
                            setMenuPosition({ top: rect.bottom + window.scrollY, right: window.innerWidth - rect.right });
                            setOpenMenuId(transaction.id);
                          }
                        }}
                        className="p-1 rounded hover:bg-gray-200 text-gray-500"
                      >
                        <MoreVertical className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td
                    colSpan={6}
                    className="px-6 py-12 text-center text-gray-500"
                  >
                    <div className="flex flex-col items-center">
                      <Filter className="w-12 h-12 text-gray-300 mb-2" />
                      <p>Nenhuma transação encontrada</p>
                      <p className="text-sm text-gray-400 mt-1">
                        Tente ajustar os filtros para ver mais resultados
                      </p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal de criação de transação */}
      <TransactionForm
        isOpen={showCreateForm}
        onClose={() => setShowCreateForm(false)}
        transactionType={activeTab}
        onSuccess={handleTransactionCreated}
      />

      {/* Dropdown de ações (fixo na viewport para escapar de overflow) */}
      {openMenuId && menuPosition && (
        <>
          <div className="fixed inset-0 z-20" onClick={() => { setOpenMenuId(null); setMenuPosition(null); }} />
          <div
            className="fixed z-30 w-52 bg-white rounded-md shadow-lg border border-gray-200"
            style={{ top: menuPosition.top, right: menuPosition.right }}
          >
            {(() => {
              const t = filteredTransactions.find(tx => tx.id === openMenuId);
              if (!t) return null;
              return (
                <>
                  <button
                    onClick={() => { handleToggleExcluded(t); setOpenMenuId(null); setMenuPosition(null); }}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    {t.excluded ? 'Incluir nas análises' : 'Excluir das análises'}
                  </button>
                  <button
                    onClick={() => { setDeleteTarget(t); setOpenMenuId(null); setMenuPosition(null); }}
                    className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                  >
                    Deletar
                  </button>
                </>
              );
            })()}
          </div>
        </>
      )}

      {/* Dialog de confirmação de delete */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center space-x-3 mb-4">
              <AlertTriangle className="w-6 h-6 text-red-600" />
              <h3 className="text-lg font-semibold text-gray-900">Confirmar Exclusão</h3>
            </div>
            <p className="text-gray-600 mb-4">
              Tem certeza que deseja deletar esta transação? Esta ação não pode ser desfeita.
            </p>
            <div className="bg-gray-50 rounded-md p-3 mb-4">
              <p className="text-sm text-gray-600 truncate" title={deleteTarget.description}>
                {deleteTarget.description}
              </p>
            </div>
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setDeleteTarget(null)}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
                disabled={isDeleting}
              >
                Cancelar
              </button>
              <button
                onClick={handleConfirmDelete}
                disabled={isDeleting}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 flex items-center space-x-2"
              >
                {isDeleting ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                ) : (
                  <Trash2 className="w-4 h-4" />
                )}
                <span>{isDeleting ? 'Deletando...' : 'Deletar'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de bulk category */}
      {showBulkCategoryModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Atualizar Categoria</h3>
            <p className="text-sm text-gray-600 mb-4">
              Atualizar categoria de <span className="font-semibold">{selectedIds.length}</span> transação(ões) selecionada(s).
            </p>
            <div className="space-y-3 mb-6">
              {bulkUniqueParents.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Grupo de Categoria
                  </label>
                  <select
                    value={bulkParentFilter}
                    onChange={(e) => {
                      setBulkParentFilter(e.target.value);
                      setBulkCategoryId('');
                    }}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="__all__">Todos os grupos</option>
                    {bulkUniqueParents.map(parent => {
                      const cat = catByDescription.get(parent);
                      return (
                        <option key={parent} value={parent}>
                          {cat ? getCategoryLabel(cat) : parent}
                        </option>
                      );
                    })}
                  </select>
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Categoria
                </label>
                <select
                  value={bulkCategoryId}
                  onChange={(e) => setBulkCategoryId(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="">Sem categoria</option>
                  {bulkFilteredCategories.map(cat => (
                    <option key={cat.id} value={cat.id}>
                      {getCategoryLabel(cat)}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowBulkCategoryModal(false);
                  setBulkCategoryId('');
                  resetBulkParentFilter();
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
              >
                Cancelar
              </button>
              <button
                onClick={handleBulkCategorySave}
                className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700"
              >
                Salvar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
