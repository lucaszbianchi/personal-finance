import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '@/services/api';
import type { NetWorth, PartialResult } from '@/types';

export const useNetWorth = () => {
  return useQuery<NetWorth>({
    queryKey: ['dashboard', 'net-worth'],
    queryFn: async () => {
      const response = await dashboardService.getNetWorth();
      return response.data;
    },
    staleTime: 1000 * 60 * 2,
  });
};

export const usePartialResult = () => {
  return useQuery<PartialResult>({
    queryKey: ['dashboard', 'partial-result'],
    queryFn: async () => {
      const response = await dashboardService.getPartialResult();
      return response.data;
    },
    staleTime: 1000 * 60 * 2,
  });
};
