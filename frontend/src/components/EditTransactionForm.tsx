import React, { useState, useEffect } from 'react';
import { useCategories } from '@/hooks/useCategories';
import { useUpdateBankTransaction, useUpdateCreditTransaction, useOperationTypes } from '@/hooks/useTransactions';
import { X, Save, CreditCard, Landmark } from 'lucide-react';
import type { CreateBankTransactionRequest, CreateCreditTransactionRequest, Category } from '@/types';

interface EditTransactionFormProps {
  isOpen: boolean;
  onClose: () => void;
  transactionType: 'bank' | 'credit';
  transaction: {
    id: string;
    description: string;
    amount: number;
    date: string;
    category_id?: string;
    type?: string;
    operation_type?: string;
    status?: string;
  };
  onSuccess?: () => void;
}

export const EditTransactionForm: React.FC<EditTransactionFormProps> = ({
  isOpen,
  onClose,
  transactionType,
  transaction,
  onSuccess,
}) => {
  const [formData, setFormData] = useState({
    description: '',
    amount: '',
    date: '',
    category_id: '',
    type: '',
    operation_type: '',
    status: 'PENDING'
  });

  const { data: categories } = useCategories();
  const { data: operationTypes } = useOperationTypes();
  const updateBankTransaction = useUpdateBankTransaction();
  const updateCreditTransaction = useUpdateCreditTransaction();

  const categoriesList: Category[] = categories || [];
  const operationTypesList: string[] = operationTypes || [];

  // Preenche o formulário com os dados da transação quando o modal abrir
  useEffect(() => {
    if (isOpen && transaction) {
      setFormData({
        description: transaction.description || '',
        amount: transaction.amount.toString() || '',
        date: transaction.date.split('\n')[0] || '',
        category_id: transaction.category_id || '',
        type: transaction.type || '',
        operation_type: transaction.operation_type || '',
        status: transaction.status || 'PENDING'
      });
    }
  }, [isOpen, transaction]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.description || !formData.amount) {
      alert('Por favor, preencha todos os campos obrigatórios');
      return;
    }

    try {
      const amount = parseFloat(formData.amount);

      if (transactionType === 'bank') {
        const bankTransactionData: Partial<CreateBankTransactionRequest> = {
          description: formData.description,
          amount,
          date: formData.date,
          category_id: formData.category_id || undefined,
          type: formData.type || undefined,
          operation_type: formData.operation_type || undefined,
        };

        await updateBankTransaction.mutateAsync({
          id: transaction.id,
          data: bankTransactionData
        });
      } else {
        const creditTransactionData: Partial<CreateCreditTransactionRequest> = {
          description: formData.description,
          amount,
          date: formData.date,
          category_id: formData.category_id || undefined,
          status: formData.status,
        };

        await updateCreditTransaction.mutateAsync({
          id: transaction.id,
          data: creditTransactionData
        });
      }

      onClose();
      onSuccess?.(); // Call success callback if provided

    } catch (error) {
      console.error('Erro ao atualizar transação:', error);
      alert('Erro ao atualizar transação. Verifique os dados e tente novamente.');
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const isLoading = updateBankTransaction.isPending || updateCreditTransaction.isPending;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
            {transactionType === 'bank' ? (
              <Landmark className="w-5 h-5 text-blue-600" />
            ) : (
              <CreditCard className="w-5 h-5 text-green-600" />
            )}
            <span>
              Editar Transação {transactionType === 'bank' ? 'Bancária' : 'de Crédito'}
            </span>
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* ID (read-only) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              ID da Transação
            </label>
            <input
              type="text"
              value={transaction.id}
              readOnly
              className="w-full border border-gray-200 rounded-md px-3 py-2 bg-gray-50 text-gray-600 cursor-default"
            />
          </div>

          {/* Descrição */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descrição *
            </label>
            <input
              type="text"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="ex: Compra no mercado"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-primary-500 focus:border-primary-500"
              required
            />
          </div>

          {/* Valor */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Valor *
            </label>
            <input
              type="number"
              step="0.01"
              name="amount"
              value={formData.amount}
              onChange={handleChange}
              placeholder="ex: -150.50"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-primary-500 focus:border-primary-500"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              Use valores negativos para despesas/débitos
            </p>
          </div>

          {/* Data */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Data *
            </label>
            <input
              type="date"
              name="date"
              value={formData.date}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-primary-500 focus:border-primary-500"
              required
            />
          </div>

          {/* Categoria */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Categoria
            </label>
            <select
              name="category_id"
              value={formData.category_id}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">Selecione uma categoria</option>
              {categoriesList.map(cat => (
                <option key={cat.id} value={cat.id}>
                  {cat.description}
                </option>
              ))}
            </select>
          </div>

          {/* Campos específicos para transações bancárias */}
          {transactionType === 'bank' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tipo de Operação
              </label>
              <select
                name="operation_type"
                value={formData.operation_type}
                onChange={handleChange}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Selecione o tipo de operação</option>
                {operationTypesList.map(operationType => (
                  <option key={operationType} value={operationType}>
                    {operationType}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Campos específicos para transações de crédito */}
          {transactionType === 'credit' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                name="status"
                value={formData.status}
                onChange={handleChange}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="PENDING">PENDING</option>
                <option value="POSTED">POSTED</option>
              </select>
            </div>
          )}

          {/* Botões */}
          <div className="flex justify-end space-x-2 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
              disabled={isLoading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 flex items-center space-x-2"
            >
              {isLoading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              ) : (
                <Save className="w-4 h-4" />
              )}
              <span>{isLoading ? 'Salvando...' : 'Salvar Alterações'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};