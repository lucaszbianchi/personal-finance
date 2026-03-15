import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { recurrencesService } from '@/services/api';
import type { Recurrence, RecurrenceMonthly, InstallmentItem, YearlyEntry, RecurrenceDetail } from '@/types';

export const useRecurrences = () => {
  return useQuery<Recurrence[]>({
    queryKey: ['recurrences'],
    queryFn: async () => {
      const response = await recurrencesService.getAll();
      return response.data;
    },
    staleTime: 1000 * 60 * 2,
  });
};

export const useRecurrenceMonthly = (month: string) => {
  return useQuery<RecurrenceMonthly>({
    queryKey: ['recurrences', 'monthly', month],
    queryFn: async () => {
      const response = await recurrencesService.getMonthly(month);
      return response.data;
    },
    staleTime: 1000 * 60 * 2,
  });
};

export const useRecurrenceYearly = (year: number) => {
  return useQuery<YearlyEntry[]>({
    queryKey: ['recurrences', 'yearly', year],
    queryFn: async () => {
      const response = await recurrencesService.getYearly(year);
      return response.data;
    },
    staleTime: 1000 * 60 * 5,
  });
};

export const useRecurrenceInstallments = (month: string) => {
  return useQuery<InstallmentItem[]>({
    queryKey: ['recurrences', 'installments', month],
    queryFn: async () => {
      const response = await recurrencesService.getInstallments(month);
      return response.data;
    },
    staleTime: 1000 * 60 * 2,
  });
};

export const useCreateRecurrence = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => recurrencesService.create(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['recurrences'] }),
  });
};

export const useUpdateRecurrence = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      recurrencesService.update(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['recurrences'] }),
  });
};

export const useDeleteRecurrence = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => recurrencesService.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['recurrences'] }),
  });
};

export const useToggleUnavoidable = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => recurrencesService.toggleUnavoidable(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['recurrences'] }),
  });
};

export const useMatchCount = (
  params: { merchant_name?: string; amount_min?: number; amount_max?: number; next_occurrence?: string; frequency?: string },
  enabled: boolean
) =>
  useQuery({
    queryKey: ['recurrences', 'match-count', params],
    queryFn: async () => (await recurrencesService.countMatching(params)).data,
    enabled,
    staleTime: 0,
  });

export const useRecurrenceDetail = (id: string | null) =>
  useQuery<RecurrenceDetail>({
    queryKey: ['recurrences', 'detail', id],
    queryFn: async () => (await recurrencesService.getDetail(id!)).data,
    enabled: Boolean(id),
    staleTime: 1000 * 60 * 2,
  });
