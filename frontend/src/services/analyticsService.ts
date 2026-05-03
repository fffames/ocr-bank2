import api from './api';

export interface SalaryConfig {
  default_salary_amount: number;
  salary_day_of_month: number;
  salary_category: string;
}

export interface ManualIncome {
  amount: number;
  category: string;
  income_date: string; // ISO date string
  note?: string;
}

export interface IncomeCategory {
  id?: number;
  name: string;
  description?: string;
  color?: string;
}

export interface AnalyticsStats {
  period: string;
  total_receipts: number;
  total_amount: number;
  sending_amount: number;
  receiving_amount: number;
  pending_count: number;
  reviewed_count: number;
  confirmed_count: number;
  sending_count: number;
  receiving_count: number;
  income_by_category?: Array<{
    category: string;
    total_amount: number;
    count: number;
  }>;
}

export const analyticsService = {
  // Salary endpoints
  getSalaryConfig: async (): Promise<SalaryConfig> => {
    const response = await api.get('/salary/config');
    return response.data;
  },

  updateSalaryConfig: async (config: SalaryConfig): Promise<{
    message: string;
    config: SalaryConfig;
    updated_current_month_salary?: { id: number; amount: number; date: string };
  }> => {
    const response = await api.put('/salary/config', config);
    return response.data;
  },

  checkAndGenerateSalary: async (year?: number, month?: number): Promise<{
    status: 'no_config' | 'already_exists' | 'created';
    message: string;
    salary_entry?: { id: number; amount: number; date: string };
  }> => {
    const params: any = {};
    if (year !== undefined) params.year = year;
    if (month !== undefined) params.month = month;

    const response = await api.get('/salary/check-and-generate', { params });
    return response.data;
  },

  getSalaryHistory: async (year?: number): Promise<Array<{
    id: number;
    amount: number;
    date: string;
    category: string;
    note: string;
    created_at: string | null;
  }>> => {
    const params = year ? { year } : {};
    const response = await api.get('/salary/history', { params });
    return response.data;
  },

  deleteSalary: async (salaryId: number): Promise<{ message: string }> => {
    const response = await api.delete(`/receipts/${salaryId}`);
    return response.data;
  },

  // Income category endpoints
  getIncomeCategories: async (): Promise<IncomeCategory[]> => {
    const response = await api.get('/income-categories');
    return response.data;
  },

  createIncomeCategory: async (category: Omit<IncomeCategory, 'id'>): Promise<IncomeCategory> => {
    const response = await api.post('/income-categories', category);
    return response.data;
  },

  deleteIncomeCategory: async (categoryId: number): Promise<{ message: string }> => {
    const response = await api.delete(`/income-categories/${categoryId}`);
    return response.data;
  },

  // Manual income endpoints
  getIncomeForMonth: async (year: number, month: number): Promise<Array<{
    id: number;
    amount: number;
    date: string;
    category: string;
    note: string;
    is_salary: boolean;
  }>> => {
    const response = await api.get(`/income/${year}/${month}`);
    return response.data;
  },

  createManualIncome: async (income: ManualIncome): Promise<{
    id: number;
    amount: number;
    date: string;
    category: string;
    note: string;
  }> => {
    const response = await api.post('/income', income);
    return response.data;
  },

  updateIncome: async (
    incomeId: number,
    income: Partial<ManualIncome>
  ): Promise<{
    id: number;
    amount: number;
    date: string;
    category: string;
    note: string;
  }> => {
    const response = await api.put(`/income/${incomeId}`, income);
    return response.data;
  },

  deleteIncome: async (incomeId: number): Promise<{ message: string }> => {
    const response = await api.delete(`/income/${incomeId}`);
    return response.data;
  },

  // Analytics stats endpoint
  getAnalyticsStats: async (year?: number, month?: number): Promise<AnalyticsStats> => {
    const params: Record<string, number> = {};
    if (year) params.year = year;
    if (month) params.month = month;

    const response = await api.get('/receipts/stats/overview', { params });
    return response.data;
  },
};
