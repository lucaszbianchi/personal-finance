// Base interfaces
export interface Transaction {
  id: string;
  account_id: string;
  description: string;
  amount: number;
  date: string;
  category_id?: string;
  subcategory?: string;
  split_info?: SplitInfo;
  created_at: string;
  updated_at: string;
}

export interface BankTransaction extends Transaction {
  type: 'bank';
  balance: number;
}

export interface CreditTransaction extends Transaction {
  type: 'credit';
  installments?: number;
  installment_number?: number;
}

export interface SplitInfo {
  partners: Array<{
    person_id: string;
    share: number;
  }>;
  settled_up: boolean;
}

export interface Category {
  id: string;
  description: string;
  description_translated: string | null;
  parent_id: string | null;
  parent_description: string | null;
  transaction_count: number;
}

export interface Person {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface Investment {
  id: string;
  name: string;
  type: string;
  subtype: string;
  amount: number;
  balance: number;
  date: string;
  due_date: string;
  issuer: string;
  rate_type: string;
}

export interface InvestmentHistoryEntry {
  month: string;
  investments: Record<string, number>;
  by_type: Record<string, number>;
  total: number;
}

export interface FinanceSummary {
  total_income: number;
  total_expenses: number;
  net_balance: number;
  period: string;
  categories_breakdown: Array<{
    category: string;
    amount: number;
    percentage: number;
  }>;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// Form interfaces
export interface TransactionFilter {
  start_date?: string;
  end_date?: string;
  category_id?: string;
  account_id?: string;
  description?: string;
  min_amount?: number;
  max_amount?: number;
}

export interface CreateTransactionRequest {
  account_id: string;
  description: string;
  amount: number;
  date: string;
  category_id?: string;
  subcategory?: string;
}

export interface CreateBankTransactionRequest {
  id: string;
  description: string;
  amount: number;
  date: string;
  category_id?: string;
  type?: string;
  operation_type?: string;
  split_info?: any;
  payment_data?: any;
}

export interface CreateCreditTransactionRequest {
  id: string;
  description: string;
  amount: number;
  date: string;
  category_id?: string;
  status?: string;
}

// Dashboard types
export interface CategoryBreakdownItem {
  id: string;
  description: string;
  total: number;
}

export interface HistoryEntry {
  month: string;
  income: number | null;
  expenses: number | null;
  investments: number | null;
}

export interface DashboardData {
  current_month: {
    income: number | null;
    expenses: number | null;
    balance: number | null;
    credit_card_bill: number | null;
    total_cash: number | null;
  };
  category_breakdown: CategoryBreakdownItem[];
  history: HistoryEntry[];
}

// Summary types
export interface MonthlySummary {
  current: {
    month: string;
    income: number;
    expenses: number;
    balance: number;
    credit_card_bill: number | null;
    category_breakdown: CategoryBreakdownItem[];
  };
  previous: {
    month: string;
    income: number | null;
    expenses: number | null;
    balance: number | null;
  };
  comparison: {
    income_delta_pct: number | null;
    expenses_delta_pct: number | null;
    balance_delta_pct: number | null;
  };
}

export interface NetWorthHistoryEntry {
  month: string;
  net_worth: number;
}

export interface NetWorth {
  checking_balance: number;
  investments_total: number;
  net_worth: number;
  history: NetWorthHistoryEntry[];
}

export interface PartialResult {
  income_so_far: number;
  expenses_so_far: number;
  partial_balance: number;
  monthly_balance_goal: number | null;
  goal_pct: number | null;
}

export interface SpendingPaceDayEntry {
  day: number;
  cumulative_amount: number;
  prev_month_cumulative: number;
}

export interface SpendingPace {
  daily_series: SpendingPaceDayEntry[];
  monthly_goal: number | null;
  monthly_avg: number | null;
  unavoidable_avg: number | null;
}

export interface Recurrence {
  id: string;
  description: string | null;
  amount: number | null;
  frequency: string | null;
  next_occurrence: string | null;
  category_id: string | null;
  merchant_name: string | null;
  amount_min: number | null;
  amount_max: number | null;
  confidence: number | null;
  source: string;
  is_unavoidable: number;
  synced_at: string | null;
}

export interface RecurrenceDetail {
  recurrence: Recurrence;
  linked_transactions: Array<{ id: string; date: string; description: string; amount: number }>;
  timeline: Array<{ month: string; matched: boolean }>;
  metrics: {
    last_amount: number | null;
    avg_amount: number | null;
    total_this_year: number | null;
    last_payment_date: string | null;
  };
}

export interface InstallmentItem {
  id: string;
  description: string | null;
  category_id: string | null;
  amount: number;
  installment_number: number | null;
  total_installments: number | null;
  pct_paid: number;
  date: string;
}

export interface RecurrenceMonthly {
  installments: { total: number; items: InstallmentItem[] };
  fixed_expenses: { total: number; items: Recurrence[] };
  history: { month: string; installments: number; fixed: number }[];
}

export interface YearlyEntry {
  month: string;
  installments: number;
  fixed: number;
  projected: boolean;
}

export interface IncomeSource {
  id: string;
  description: string | null;
  amount: number | null;
  frequency: string | null;
  next_occurrence: string | null;
  category_id: string | null;
  merchant_name: string | null;
  amount_min: number | null;
  amount_max: number | null;
  confidence: number | null;
  source: string;
  synced_at: string | null;
}

export interface IncomeMonthly {
  sources: { total: number; items: IncomeSource[] };
  history: { month: string; total: number }[];
}

export interface IncomeYearlyEntry {
  month: string;
  total: number;
}

export type BillClassification = 'installment' | 'recurrent' | 'one_off';

export interface BillTransaction {
  id: string;
  description: string | null;
  amount: number;
  date: string | null;
  category_id: string | null;
  classification: BillClassification;
}

export interface BillsMonthly {
  month: string;
  total: number;
  installments: number;
  recurrent: number;
  one_off: number;
  is_open: boolean | null;
  payment_date: string | null;
  transactions: BillTransaction[];
  is_projected: boolean;
}

export interface BillsHistoryEntry {
  month: string;
  total: number;
}

export interface IncomeDetail {
  source: IncomeSource;
  linked_transactions: Array<{ id: string; date: string; description: string; amount: number }>;
  timeline: Array<{ month: string; matched: boolean }>;
  metrics: {
    last_amount: number | null;
    avg_amount: number | null;
    total_this_year: number;
    last_received_date: string | null;
  };
}
