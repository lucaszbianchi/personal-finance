import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '@/services/api';
import type { SpendingPace } from '@/types';

export const useSpendingPace = (month?: string) => {
  return useQuery<SpendingPace>({
    queryKey: ['dashboard', 'spending-pace', month],
    queryFn: async () => {
      const response = await dashboardService.getSpendingPace(month);
      return response.data;
    },
    staleTime: 1000 * 60 * 2,
  });
};
