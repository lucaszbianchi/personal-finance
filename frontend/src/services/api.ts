import axios from 'axios';
import type {
  ApiResponse,
  Transaction,
  Category,
  Person,
  Investment,
  FinanceSummary,
  TransactionFilter,
  CreateTransactionRequest,
} from '@/types';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
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
  (response) => response.data,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const transactionService = {
  getAll: (filters?: TransactionFilter) =>
    api.get<ApiResponse<Transaction[]>>('/transactions', { params: filters }),

  getById: (id: string) =>
    api.get<ApiResponse<Transaction>>(`/transactions/${id}`),

  create: (transaction: CreateTransactionRequest) =>
    api.post<ApiResponse<Transaction>>('/transactions', transaction),

  update: (id: string, transaction: Partial<Transaction>) =>
    api.put<ApiResponse<Transaction>>(`/transactions/${id}`, transaction),

  delete: (id: string) =>
    api.delete<ApiResponse<void>>(`/transactions/${id}`),
};

export const categoryService = {
  getAll: () =>
    api.get<Category[]>('/categories/'),

  getById: (id: string) =>
    api.get<ApiResponse<Category>>(`/categories/${id}/`),

  create: (category: Omit<Category, 'id' | 'created_at' | 'updated_at'>) =>
    api.post<ApiResponse<Category>>('/categories/', category),

  update: (id: string, category: Partial<Category>) =>
    api.put<ApiResponse<Category>>(`/categories/${id}/`, category),

  delete: (id: string) =>
    api.delete<ApiResponse<void>>(`/categories/${id}/`),
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
  getAll: () =>
    api.get<ApiResponse<Investment[]>>('/investments'),

  getById: (id: string) =>
    api.get<ApiResponse<Investment>>(`/investments/${id}`),
};

export const summaryService = {
  getFinanceSummary: (period?: string) =>
    api.get<ApiResponse<FinanceSummary>>('/summary/finance', {
      params: period ? { period } : {}
    }),

  getDashboardData: () =>
    api.get<ApiResponse<any>>('/dashboard'),
};

export interface SyncResponse {
  status: 'success' | 'error';
  message: string;
  counts?: {
    bank_transactions_inserted: number;
    bank_transactions_updated: number;
    credit_transactions_inserted: number;
    credit_transactions_updated: number;
    investments_inserted: number;
    investments_updated: number;
    splitwise_inserted: number;
    splitwise_updated: number;
  };
}

export const importService = {
  syncData: (): Promise<SyncResponse> =>
    api.post('/import/data'),

  importSplitwise: (): Promise<ApiResponse<void>> =>
    api.post('/import/splitwise'),
};

export default api;