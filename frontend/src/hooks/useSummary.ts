import { useQuery } from '@tanstack/react-query';
import { summaryService } from '@/services/api';
import type { MonthlySummary } from '@/types';

export const useFinanceSummary = (period?: string) => {
  return useQuery({
    queryKey: ['summary', 'finance', period],
    queryFn: () => summaryService.getFinanceSummary(period),
  });
};

export const useMonthlySummary = (month?: string) => {
  return useQuery<MonthlySummary>({
    queryKey: ['summary', 'monthly', month],
    queryFn: async () => {
      const response = await summaryService.getMonthlySummary(month);
      return response.data;
    },
    staleTime: 1000 * 60 * 2,
  });
};

