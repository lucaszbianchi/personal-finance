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
  getAll: async (filters?: TransactionFilter) => {
    const response = await api.get('/transactions', { params: filters });
    return response.data;
  },

  getById: async (id: string) => {
    const response = await api.get(`/transactions/${id}`);
    return response.data;
  },

  create: async (transaction: CreateTransactionRequest) => {
    const response = await api.post('/transactions', transaction);
    return response.data;
  },

  update: async (id: string, transaction: Partial<Transaction>) => {
    const response = await api.put(`/transactions/${id}`, transaction);
    return response.data;
  },

  delete: async (id: string) => {
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

  create: async (category: Omit<Category, 'id'>) => {
    const response = await api.post('/categories/', category);
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
  syncData: async (): Promise<SyncResponse> => {
    const response = await api.post('/import/data');
    return response.data;
  },

  importSplitwise: async (): Promise<ApiResponse<void>> => {
    const response = await api.post('/import/splitwise');
    return response.data;
  },
};

export default api;