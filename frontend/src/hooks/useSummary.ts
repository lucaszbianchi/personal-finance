import { useQuery } from '@tanstack/react-query';
import { summaryService } from '@/services/api';

export const useFinanceSummary = (period?: string) => {
  return useQuery({
    queryKey: ['summary', 'finance', period],
    queryFn: () => summaryService.getFinanceSummary(period),
  });
};

export const useDashboardData = () => {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: () => summaryService.getDashboardData(),
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
};