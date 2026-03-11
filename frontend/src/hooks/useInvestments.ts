import { useQuery } from '@tanstack/react-query';
import { investmentService } from '@/services/api';

export const useInvestments = () => {
  return useQuery({
    queryKey: ['investments'],
    queryFn: () => investmentService.getAll(),
  });
};

export const useInvestmentHistory = () => {
  return useQuery({
    queryKey: ['investments', 'history'],
    queryFn: () => investmentService.getHistory(),
  });
};
