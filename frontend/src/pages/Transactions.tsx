import React, { useState, useEffect, useMemo } from 'react';
import { useCategories } from '@/hooks/useCategories';
import { TransactionForm } from '@/components/TransactionForm';
import { EditTransactionForm } from '@/components/EditTransactionForm';
import { DeleteTransactionButton } from '@/components/DeleteTransactionButton';
import { EditTransactionButton } from '@/components/EditTransactionButton';
import { CreditCard, Landmark, Filter, X, ChevronDown, Plus } from 'lucide-react';
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
  split_info?: any;
  payment_data?: any;
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

  // Estados para formulário de criação
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Estados para edição
  const [showEditForm, setShowEditForm] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null);

  const { data: categories } = useCategories();
  const categoriesList: Category[] = useMemo(
    () => categories || [],
    [categories]
  );

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
        // Construir query string com filtros
        const params = new URLSearchParams();
        
        // Filtro de período: converter YYYY-MM para start_date e end_date
        if (selectedPeriod && selectedPeriod !== '__all__') {
          const [year, month] = selectedPeriod.split('-');
          const startDate = `${year}-${month}-01`;
          
          // Calcular último dia do mês
          const lastDay = new Date(parseInt(year), parseInt(month), 0).getDate();
          const endDate = `${year}-${month}-${String(lastDay).padStart(2, '0')}`;
          
          params.append('start_date', startDate);
          params.append('end_date', endDate);
        }
        
        // Filtro de categoria: mapear nome para ID
        if (selectedCategory && categoriesList.length > 0) {
          const category = categoriesList.find(cat => cat.name === selectedCategory);
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

  // Aplicar filtro de texto (busca) no frontend
  // Período e categoria são filtrados no backend
  useEffect(() => {
    let filtered = [...transactions];

    // Filtro por busca de texto
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(t => 
        t.description.toLowerCase().includes(search)
      );
    }

    setFilteredTransactions(filtered);
  }, [transactions, searchTerm]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatDate = (dateStr: string) => {
    const date = dateStr.split('\n')[0] || dateStr.split('T')[0];
    const [year, month, day] = date.split('-');
    return `${day}/${month}/${year}`;
  };

  const getAmountColor = (amount: number) => {
    if (activeTab === 'bank') {
      return amount > 0 ? 'text-success-600' : 'text-danger-600';
    } else {
      // Para crédito: valores positivos são despesas (vermelho)
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
    setRefreshTrigger(prev => prev + 1); // Force refresh
  };

  const handleEditTransaction = (transaction: Transaction) => {
    setEditingTransaction(transaction);
    setShowEditForm(true);
  };

  const handleTransactionUpdated = () => {
    setShowEditForm(false);
    setEditingTransaction(null);
    setRefreshTrigger(prev => prev + 1); // Force refresh
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
                {categoriesList.map(cat => (
                  <option key={cat.id} value={cat.name}>
                    {cat.name}
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
        )}

        {/* Resumo dos resultados */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-sm text-gray-600">
            Mostrando <span className="font-semibold">{filteredTransactions.length}</span> de{' '}
            <span className="font-semibold">{transactions.length}</span> transações
          </p>
        </div>
      </div>

      {/* Tabela de transações */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Data
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Descrição
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Categoria
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Valor
                </th>
                {activeTab === 'bank' && (
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tipo de Operação
                  </th>
                )}
                {activeTab === 'credit' && (
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                )}
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredTransactions.length > 0 ? (
                filteredTransactions.map((transaction) => (
                  <tr 
                    key={transaction.id} 
                    className="hover:bg-gray-50 transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(transaction.date)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <div className="max-w-md" title={transaction.description}>
                        {transaction.description}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        {transaction.category || 'Sem categoria'}
                      </span>
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm font-semibold ${getAmountColor(transaction.amount)}`}>
                      {formatCurrency(transaction.amount)}
                    </td>
                    {activeTab === 'bank' && (
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {transaction.operation_type || '-'}
                      </td>
                    )}
                    {activeTab === 'credit' && (
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {transaction.status || '-'}
                      </td>
                    )}
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                      <div className="flex justify-end space-x-2">
                        <EditTransactionButton
                          onClick={() => handleEditTransaction(transaction)}
                        />
                        <DeleteTransactionButton
                          transactionId={transaction.id}
                          transactionType={activeTab}
                          transactionDescription={transaction.description}
                          onSuccess={() => setRefreshTrigger(prev => prev + 1)}
                        />
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td
                    colSpan={activeTab === 'bank' ? 6 : 6}
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

      {/* Modal de edição de transação */}
      {editingTransaction && (
        <EditTransactionForm
          isOpen={showEditForm}
          onClose={() => {
            setShowEditForm(false);
            setEditingTransaction(null);
          }}
          transactionType={activeTab}
          transaction={{
            id: editingTransaction.id,
            description: editingTransaction.description,
            amount: editingTransaction.amount,
            date: editingTransaction.date,
            category_id: editingTransaction.category_id,
            type: editingTransaction.type,
            operation_type: editingTransaction.operation_type,
            status: editingTransaction.status,
          }}
          onSuccess={handleTransactionUpdated}
        />
      )}
    </div>
  );
};