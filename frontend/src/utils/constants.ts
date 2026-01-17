export const API_ENDPOINTS = {
  TRANSACTIONS: '/api/transactions',
  CATEGORIES: '/api/categories',
  PERSONS: '/api/persons',
  INVESTMENTS: '/api/investments',
  SUMMARY: '/api/summary',
  DASHBOARD: '/api/dashboard',
  IMPORT: '/api/import',
  SPLITWISE: '/api/splitwise',
} as const;

export const TRANSACTION_TYPES = {
  BANK: 'bank',
  CREDIT: 'credit',
} as const;

export const CATEGORY_TYPES = {
  INCOME: 'income',
  EXPENSE: 'expense',
  TRANSFER: 'transfer',
} as const;

export const QUERY_KEYS = {
  TRANSACTIONS: 'transactions',
  TRANSACTION: 'transaction',
  CATEGORIES: 'categories',
  CATEGORY: 'category',
  PERSONS: 'persons',
  PERSON: 'person',
  INVESTMENTS: 'investments',
  INVESTMENT: 'investment',
  SUMMARY: 'summary',
  DASHBOARD: 'dashboard',
} as const;

export const DATE_FORMATS = {
  ISO: 'YYYY-MM-DD',
  DISPLAY: 'DD/MM/YYYY',
  DATETIME: 'DD/MM/YYYY HH:mm',
} as const;

export const COLORS = {
  PRIMARY: '#3b82f6',
  SUCCESS: '#22c55e',
  DANGER: '#ef4444',
  WARNING: '#f59e0b',
  INFO: '#06b6d4',
  GRAY: '#6b7280',
} as const;