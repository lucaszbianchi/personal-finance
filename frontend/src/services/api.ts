import axios from 'axios';
import type {
  ApiResponse,
  Transaction,
  Person,
  Investment,
  InvestmentHistoryEntry,
  FinanceSummary,
  TransactionFilter,
  CreateTransactionRequest,
  CreateBankTransactionRequest,
  CreateCreditTransactionRequest,
  DashboardData,
  MonthlySummary,
  SpendingPace,
  NetWorth,
  PartialResult,
} from '@/types';

const api = axios.create({
  baseURL: '/api',
  timeout: 20000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const transactionService = {
  // Bank transactions
  getBankTransactions: async (filters?: TransactionFilter) => {
    const response = await api.get('/transactions/bank', { params: filters });
    return response.data;
  },

  createBankTransaction: async (transaction: CreateBankTransactionRequest) => {
    const response = await api.post('/transactions/bank', transaction);
    return response.data;
  },

  deleteBankTransaction: async (id: string) => {
    const response = await api.delete(`/transactions/bank/${id}`);
    return response.data;
  },

  // Credit transactions
  getCreditTransactions: async (filters?: TransactionFilter) => {
    const response = await api.get('/transactions/credit', { params: filters });
    return response.data;
  },

  createCreditTransaction: async (transaction: CreateCreditTransactionRequest) => {
    const response = await api.post('/transactions/credit', transaction);
    return response.data;
  },

  deleteCreditTransaction: async (id: string) => {
    const response = await api.delete(`/transactions/credit/${id}`);
    return response.data;
  },

  updateBankTransaction: async (id: string, transaction: Partial<CreateBankTransactionRequest>) => {
    const response = await api.put(`/transactions/bank/${id}`, transaction);
    return response.data;
  },

  updateCreditTransaction: async (id: string, transaction: Partial<CreateCreditTransactionRequest>) => {
    const response = await api.put(`/transactions/credit/${id}`, transaction);
    return response.data;
  },

  setExcluded: async (type: 'bank' | 'credit', id: string, excluded: boolean) => {
    const response = await api.put(`/transactions/${type}/${id}/excluded`, { excluded });
    return response.data;
  },

  getOperationTypes: async () => {
    const response = await api.get('/transactions/operation-types');
    return response.data.operation_types;
  },

  // Generic methods (for backward compatibility)
  getAll: async (filters?: TransactionFilter) => {
    const response = await api.get('/transactions', { params: filters });
    return response.data;
  },

  getById: async (id: string) => {
    const response = await api.get(`/transactions/${id}`);
    return response.data;
  },

  update: async (transactionType: 'bank' | 'credit', id: string, transaction: Partial<Transaction>) => {
    const response = await api.put(`/transactions/${transactionType}/${id}`, transaction);
    return response.data;
  },

  // Deprecated - use specific methods instead
  create: async (transaction: CreateTransactionRequest) => {
    console.warn('Using deprecated create method. Use createBankTransaction or createCreditTransaction instead.');
    const response = await api.post('/transactions', transaction);
    return response.data;
  },

  delete: async (id: string) => {
    console.warn('Using deprecated delete method. Use deleteBankTransaction or deleteCreditTransaction instead.');
    const response = await api.delete(`/transactions/${id}`);
    return response.data;
  },
};

export const categoryService = {
  getAll: async () => {
    const response = await api.get('/categories/');
    return response.data;
  },

  getById: async (id: string) => {
    const response = await api.get(`/categories/${id}`);
    return response.data;
  },

  create: async (category: { description: string; description_translated?: string | null; parent_id?: string | null; parent_description?: string | null }) => {
    const response = await api.post('/categories/', {
      name: category.description,
      description_translated: category.description_translated ?? null,
      parent_id: category.parent_id ?? null,
      parent_description: category.parent_description ?? null,
    });
    return response.data;
  },

  updateFields: async (id: string, fields: { description_translated?: string | null; parent_id?: string | null; parent_description?: string | null }) => {
    const response = await api.patch(`/categories/${id}/fields`, fields);
    return response.data;
  },

  update: async (oldName: string, newName: string) => {
    const response = await api.post('/categories/edit', { old_name: oldName, new_name: newName });
    return response.data;
  },

  delete: async (categoryName: string) => {
    const response = await api.delete(`/categories/${categoryName}`);
    return response.data;
  },

  unify: async (categories: string[], target: string) => {
    const response = await api.post('/categories/unify', { categories, target });
    return response.data;
  },

};

export const personService = {
  getAll: () =>
    api.get<ApiResponse<Person[]>>('/persons'),

  getById: (id: string) =>
    api.get<ApiResponse<Person>>(`/persons/${id}`),

  create: (person: Omit<Person, 'id' | 'created_at' | 'updated_at'>) =>
    api.post<ApiResponse<Person>>('/persons', person),

  update: (id: string, person: Partial<Person>) =>
    api.put<ApiResponse<Person>>(`/persons/${id}`, person),

  delete: (id: string) =>
    api.delete<ApiResponse<void>>(`/persons/${id}`),
};

export const investmentService = {
  getAll: async (): Promise<Investment[]> => {
    const response = await api.get('/investments/');
    return response.data;
  },

  getHistory: async (): Promise<InvestmentHistoryEntry[]> => {
    const response = await api.get('/investments/history');
    return response.data;
  },
};

export const summaryService = {
  getFinanceSummary: (period?: string) =>
    api.get<ApiResponse<FinanceSummary>>('/summary/finance', {
      params: period ? { period } : {}
    }),

  getMonthlySummary: (month?: string) =>
    api.get<MonthlySummary>('/summary/monthly', {
      params: month ? { month } : {},
    }),
};

export const dashboardService = {
  getDashboardData: () =>
    api.get<DashboardData>('/dashboard/data'),

  getSpendingPace: (month?: string) =>
    api.get<SpendingPace>('/dashboard/spending-pace', {
      params: month ? { month } : {},
    }),

  getNetWorth: () =>
    api.get<NetWorth>('/overview/net-worth'),

  getPartialResult: () =>
    api.get<PartialResult>('/overview/partial-result'),
};

export type ImportType = 'recent' | 'non_recent';

export interface RateLimitUsage {
  call_type: string;
  year_month: string;
  count: number;
  limit_value: number;
  remaining: number;
  exceeded: boolean;
}

export interface SyncResponse {
  status: 'success' | 'error';
  message: string;
  rate_limit_warning?: string;
  counts?: {
    bank_transactions_inserted: number;
    bank_transactions_updated: number;
    credit_transactions_inserted: number;
    credit_transactions_updated: number;
    investments_inserted: number;
    investments_updated: number;
    splitwise_inserted: number;
    splitwise_updated: number;
    rate_limit_usage: RateLimitUsage[];
  };
}

export const importService = {
  syncData: async (importType: ImportType = 'recent'): Promise<SyncResponse> => {
    const response = await api.post('/import/data', { import_type: importType }, { timeout: 120000 });
    return response.data;
  },

  importSplitwise: async (): Promise<ApiResponse<void>> => {
    const response = await api.post('/import/splitwise');
    return response.data;
  },
};

export const databaseService = {
  reset: () => api.post('/database/reset'),
};

export const recurrencesService = {
  getAll: () => api.get('/recurrences'),
  create: (data: Record<string, unknown>) => api.post('/recurrences', data),
  update: (id: string, data: Record<string, unknown>) => api.put(`/recurrences/${id}`, data),
  remove: (id: string) => api.delete(`/recurrences/${id}`),
  toggleUnavoidable: (id: string) => api.patch(`/recurrences/${id}/toggle-unavoidable`),
  getMonthly: (month: string) => api.get('/recurrences/monthly', { params: { month } }),
  getInstallments: (month: string) => api.get('/recurrences/installments', { params: { month } }),
  getYearly: (year: number) => api.get('/recurrences/yearly', { params: { year } }),
  countMatching: (p: { merchant_name?: string; amount_min?: number; amount_max?: number; next_occurrence?: string; frequency?: string }) =>
    api.get<{ count: number }>('/recurrences/match-count', { params: p }),
  getDetail: (id: string) =>
    api.get(`/recurrences/${id}/detail`),
};

export const incomeService = {
  getAll: () => api.get('/income/sources'),
  create: (data: Record<string, unknown>) => api.post('/income/sources', data),
  update: (id: string, data: Record<string, unknown>) => api.put(`/income/sources/${id}`, data),
  remove: (id: string) => api.delete(`/income/sources/${id}`),
  getDetail: (id: string) => api.get(`/income/sources/${id}/detail`),
  countMatching: (p: { merchant_name?: string; amount_min?: number; amount_max?: number; next_occurrence?: string; frequency?: string }) =>
    api.get<{ count: number }>('/income/match-count', { params: p }),
  getMonthly: (month: string) => api.get('/income/monthly', { params: { month } }),
  getYearly: (year: number) => api.get('/income/yearly', { params: { year } }),
};

export const cashFlowService = {
  getCashFlow: (window: 3 | 6, endMonth?: string) =>
    api.get('/cash-flow', { params: { window, ...(endMonth ? { end_month: endMonth } : {}) } }),
};

export const billsService = {
  getMonthly: (month: string) => api.get('/bills/monthly', { params: { month } }),
  getHistory: () => api.get('/bills/history'),
};

export default api;
