import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '@/services/api';
import type { DashboardData } from '@/types';

export const useDashboardData = () => {
  return useQuery<DashboardData>({
    queryKey: ['dashboard', 'data'],
    queryFn: async () => {
      const response = await dashboardService.getDashboardData();
      return response.data;
    },
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
};
