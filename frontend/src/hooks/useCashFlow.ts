import { useQuery } from '@tanstack/react-query';
import { cashFlowService } from '@/services/api';

export interface CashFlowMonthValue {
  month: string;
  value: number | null;
}

export interface CashFlowMonthCategories {
  month: string;
  categories: Record<string, number>;
}

export interface CashFlowWindow {
  months: string[];
  net_balance: CashFlowMonthValue[];
  income: CashFlowMonthValue[];
  period_total: number | null;
}

export interface CashFlowCurrentWindow extends CashFlowWindow {
  expenses_by_category: CashFlowMonthCategories[];
}

export interface CashFlowPreviousWindow extends CashFlowWindow {
  delta_pct: number | null;
}

export interface CashFlowData {
  current_window: CashFlowCurrentWindow;
  previous_window: CashFlowPreviousWindow;
}

export function useCashFlow(window: 3 | 6, endMonth?: string) {
  return useQuery<CashFlowData>({
    queryKey: ['cash-flow', window, endMonth],
    queryFn: () => cashFlowService.getCashFlow(window, endMonth).then(r => r.data),
    staleTime: 2 * 60 * 1000,
  });
}
