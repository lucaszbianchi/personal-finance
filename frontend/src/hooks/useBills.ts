import { useQuery } from '@tanstack/react-query';
import { billsService } from '@/services/api';
import type { BillsMonthly, BillsHistoryEntry } from '@/types';

export function useBillsMonthly(month: string) {
  return useQuery<BillsMonthly>({
    queryKey: ['bills', 'monthly', month],
    queryFn: () => billsService.getMonthly(month).then(r => r.data),
    staleTime: 1000 * 60 * 2,
  });
}

export function useBillsHistory() {
  return useQuery<BillsHistoryEntry[]>({
    queryKey: ['bills', 'history'],
    queryFn: () => billsService.getHistory().then(r => r.data),
    staleTime: 1000 * 60 * 5,
  });
}
