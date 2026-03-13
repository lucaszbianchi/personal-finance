import React, { useState } from 'react';
import { useDeleteBankTransaction, useDeleteCreditTransaction } from '@/hooks/useTransactions';
import { Trash2, AlertTriangle } from 'lucide-react';

interface DeleteTransactionButtonProps {
  transactionId: string;
  transactionType: 'bank' | 'credit';
  transactionDescription: string;
  className?: string;
  onSuccess?: () => void;
  asMenuItem?: boolean;
}

export const DeleteTransactionButton: React.FC<DeleteTransactionButtonProps> = ({
  transactionId,
  transactionType,
  transactionDescription,
  className = '',
  onSuccess,
  asMenuItem = false,
}) => {
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  const deleteBankTransaction = useDeleteBankTransaction();
  const deleteCreditTransaction = useDeleteCreditTransaction();

  const isLoading = deleteBankTransaction.isPending || deleteCreditTransaction.isPending;

  const handleDelete = async () => {
    try {
      if (transactionType === 'bank') {
        await deleteBankTransaction.mutateAsync(transactionId);
      } else {
        await deleteCreditTransaction.mutateAsync(transactionId);
      }
      setShowConfirmDialog(false);
      onSuccess?.(); // Call success callback if provided
    } catch (error) {
      console.error('Erro ao deletar transação:', error);
      alert('Erro ao deletar transação. Tente novamente.');
    }
  };

  return (
    <>
      {asMenuItem ? (
        <button
          onClick={() => setShowConfirmDialog(true)}
          className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
          disabled={isLoading}
        >
          Deletar
        </button>
      ) : (
        <button
          onClick={() => setShowConfirmDialog(true)}
          className={`text-red-600 hover:text-red-800 ${className}`}
          title="Deletar transação"
          disabled={isLoading}
        >
          <Trash2 className="w-4 h-4" />
        </button>
      )}

      {/* Dialog de confirmação */}
      {showConfirmDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center space-x-3 mb-4">
              <AlertTriangle className="w-6 h-6 text-red-600" />
              <h3 className="text-lg font-semibold text-gray-900">
                Confirmar Exclusão
              </h3>
            </div>

            <p className="text-gray-600 mb-4">
              Tem certeza que deseja deletar esta transação? Esta ação não pode ser desfeita.
            </p>

            <div className="bg-gray-50 rounded-md p-3 mb-4">
              <p className="text-sm font-medium text-gray-700">Transação:</p>
              <p className="text-sm text-gray-600 truncate" title={transactionDescription}>
                {transactionDescription}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                ID: {transactionId}
              </p>
            </div>

            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setShowConfirmDialog(false)}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
                disabled={isLoading}
              >
                Cancelar
              </button>
              <button
                onClick={handleDelete}
                disabled={isLoading}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 flex items-center space-x-2"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Deletando...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    <span>Deletar</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};