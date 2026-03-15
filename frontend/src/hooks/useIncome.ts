import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { incomeService } from '@/services/api';
import type { IncomeMonthly, IncomeYearlyEntry, IncomeDetail } from '@/types';

export const useIncomeMonthly = (month: string) =>
  useQuery<IncomeMonthly>({
    queryKey: ['income', 'monthly', month],
    queryFn: async () => (await incomeService.getMonthly(month)).data,
    staleTime: 1000 * 60 * 2,
  });

export const useIncomeYearly = (year: number) =>
  useQuery<IncomeYearlyEntry[]>({
    queryKey: ['income', 'yearly', year],
    queryFn: async () => (await incomeService.getYearly(year)).data,
    staleTime: 1000 * 60 * 5,
  });

export const useCreateIncomeSource = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => incomeService.create(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['income'] }),
  });
};

export const useUpdateIncomeSource = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      incomeService.update(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['income'] }),
  });
};

export const useDeleteIncomeSource = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => incomeService.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['income'] }),
  });
};

export const useIncomeDetail = (id: string | null) =>
  useQuery<IncomeDetail>({
    queryKey: ['income', 'detail', id],
    queryFn: async () => (await incomeService.getDetail(id!)).data,
    enabled: Boolean(id),
    staleTime: 1000 * 60 * 2,
  });

export const useIncomeMatchCount = (
  params: { merchant_name?: string; amount_min?: number; amount_max?: number; next_occurrence?: string; frequency?: string },
  enabled: boolean
) =>
  useQuery({
    queryKey: ['income', 'match-count', params],
    queryFn: async () => (await incomeService.countMatching(params)).data,
    enabled,
    staleTime: 0,
  });
