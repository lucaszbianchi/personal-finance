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
  name: string;
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
  value: number;
  date: string;
  created_at: string;
  updated_at: string;
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