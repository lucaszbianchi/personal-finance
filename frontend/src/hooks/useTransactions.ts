import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { transactionService } from '@/services/api';
import type { TransactionFilter, CreateTransactionRequest, Transaction, CreateBankTransactionRequest, CreateCreditTransactionRequest } from '@/types';

export const useTransactions = (filters?: TransactionFilter) => {
  return useQuery({
    queryKey: ['transactions', filters],
    queryFn: () => transactionService.getAll(filters),
  });
};

export const useTransaction = (id: string) => {
  return useQuery({
    queryKey: ['transaction', id],
    queryFn: () => transactionService.getById(id),
    enabled: !!id,
  });
};

export const useCreateTransaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (transaction: CreateTransactionRequest) =>
      transactionService.create(transaction),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['summary'] });
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
  });
};

export const useUpdateTransaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ transactionType, id, data }: { transactionType: 'bank' | 'credit'; id: string; data: Partial<Transaction> }) =>
      transactionService.update(transactionType, id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['transaction', id] });
      queryClient.invalidateQueries({ queryKey: ['summary'] });
    },
  });
};

export const useDeleteTransaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => transactionService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['summary'] });
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
  });
};

// Specific hooks for bank transactions
export const useBankTransactions = (filters?: TransactionFilter) => {
  return useQuery({
    queryKey: ['bank-transactions', filters],
    queryFn: () => transactionService.getBankTransactions(filters),
  });
};

export const useCreateBankTransaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (transaction: CreateBankTransactionRequest) =>
      transactionService.createBankTransaction(transaction),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bank-transactions'] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['summary'] });
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
  });
};

export const useDeleteBankTransaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => transactionService.deleteBankTransaction(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bank-transactions'] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['summary'] });
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
  });
};

// Specific hooks for credit transactions
export const useCreditTransactions = (filters?: TransactionFilter) => {
  return useQuery({
    queryKey: ['credit-transactions', filters],
    queryFn: () => transactionService.getCreditTransactions(filters),
  });
};

export const useCreateCreditTransaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (transaction: CreateCreditTransactionRequest) =>
      transactionService.createCreditTransaction(transaction),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credit-transactions'] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['summary'] });
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
  });
};

export const useDeleteCreditTransaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => transactionService.deleteCreditTransaction(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credit-transactions'] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['summary'] });
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
  });
};

export const useUpdateBankTransaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateBankTransactionRequest> }) =>
      transactionService.updateBankTransaction(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bank-transactions'] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['summary'] });
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
  });
};

export const useUpdateCreditTransaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateCreditTransactionRequest> }) =>
      transactionService.updateCreditTransaction(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credit-transactions'] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['summary'] });
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
  });
};

export const useToggleExcluded = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ type, id, excluded }: { type: 'bank' | 'credit'; id: string; excluded: boolean }) =>
      transactionService.setExcluded(type, id, excluded),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bank-transactions'] });
      queryClient.invalidateQueries({ queryKey: ['credit-transactions'] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['summary'] });
    },
  });
};

export const useOperationTypes = () => {
  return useQuery({
    queryKey: ['operation-types'],
    queryFn: () => transactionService.getOperationTypes(),
    staleTime: 5 * 60 * 1000, // 5 minutes - operation types don't change frequently
  });
};