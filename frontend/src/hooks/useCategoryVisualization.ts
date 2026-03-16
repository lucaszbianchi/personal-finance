import { useQuery } from '@tanstack/react-query';
import { categoryVizService } from '@/services/api';
import type { CategoryDistribution, CategoryExpenseHistory } from '@/types';

export const useCategoryExpenseHistory = (months = 6) => {
  return useQuery<CategoryExpenseHistory>({
    queryKey: ['category-expense-history', months],
    queryFn: async () => {
      const res = await categoryVizService.getExpenseHistory(months);
      return res.data;
    },
  });
};

export const useCategoryDistribution = (month: string) => {
  return useQuery<CategoryDistribution>({
    queryKey: ['category-distribution', month],
    queryFn: async () => {
      const res = await categoryVizService.getDistribution(month);
      return res.data;
    },
    enabled: !!month,
  });
};
