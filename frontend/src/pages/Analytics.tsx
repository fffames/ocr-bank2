import { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Calendar,
  BarChart3,
  ArrowDownRight
} from 'lucide-react';
import { analyticsService, AnalyticsStats } from '../services/analyticsService';

interface IncomeEntry {
  id: number;
  amount: number;
  date: string;
  category: string;
  note: string;
  is_salary: boolean;
}

export default function AnalyticsPage() {
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [currentMonth, setCurrentMonth] = useState(new Date().getMonth() + 1);
  const [stats, setStats] = useState<AnalyticsStats | null>(null);
  const [incomeEntries, setIncomeEntries] = useState<IncomeEntry[]>([]);
  const [expenseEntries, setExpenseEntries] = useState<Array<any>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [currentYear, currentMonth]);

  const loadData = async () => {
    setLoading(true);
    try {
      // Load stats
      const statsData = await analyticsService.getAnalyticsStats(currentYear, currentMonth);
      setStats(statsData);

      // Load income entries
      const incomeData = await analyticsService.getIncomeForMonth(currentYear, currentMonth);
      setIncomeEntries(incomeData);

      // Load expense entries
      await loadExpenseEntries();
    } catch (error) {
      console.error('Failed to load analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadExpenseEntries = async () => {
    try {
      // Get all expense receipts for the selected month
      const { receiptService } = await import('../services/receiptService');

      // Fetch with date range filter for the selected month
      const startDate = new Date(currentYear, currentMonth - 1, 1);
      const endDate = new Date(currentYear, currentMonth, 0); // Last day of month

      // Format dates as YYYY-MM-DD to avoid timezone issues
      const formatDate = (date: Date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
      };

      const params: any = {
        date_from: formatDate(startDate),
        date_to: formatDate(endDate),
        transaction_type: 'sending',
        limit: 1000
      };

      console.log('📅 Expense filter params:', params);
      const expenses = await receiptService.getReceipts(params);
      console.log('💰 Expense entries loaded:', expenses.length, 'items');
      setExpenseEntries(expenses);
    } catch (error) {
      console.error('Failed to load expense entries:', error);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('th-TH', {
      style: 'currency',
      currency: 'THB'
    }).format(amount);
  };

  const getMonthName = (month: number) => {
    const months = ['January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'];
    return months[month - 1];
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Loading analytics...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        <BarChart3 className="text-blue-600" size={32} />
      </div>

      {/* Year/Month Filter */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex items-center gap-4">
          <Calendar className="text-gray-600" size={20} />
          <label className="text-sm font-medium text-gray-700">Period:</label>
          <select
            value={currentYear}
            onChange={(e) => setCurrentYear(parseInt(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            {Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i).map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
          <select
            value={currentMonth}
            onChange={(e) => setCurrentMonth(parseInt(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            {Array.from({ length: 12 }, (_, i) => i + 1).map(month => (
              <option key={month} value={month}>{getMonthName(month)}</option>
            ))}
          </select>
        </div>
      </div>

      {stats && (
        <>
          {/* Overview Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Net Amount</p>
                  <p className={`text-2xl font-bold ${stats.total_amount >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(stats.total_amount)}
                  </p>
                </div>
                <TrendingUp className="text-blue-600" size={24} />
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Income</p>
                  <p className="text-2xl font-bold text-green-600">
                    {formatCurrency(stats.receiving_amount)}
                  </p>
                </div>
                <TrendingUp className="text-green-600" size={24} />
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Expenses</p>
                  <p className="text-2xl font-bold text-red-600">
                    {formatCurrency(stats.sending_amount)}
                  </p>
                </div>
                <TrendingDown className="text-red-600" size={24} />
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Transactions</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {stats.total_receipts}
                  </p>
                </div>
                <BarChart3 className="text-gray-600" size={24} />
              </div>
            </div>
          </div>

          {/* Income & Expense Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Income Breakdown by Category */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Income Breakdown</h2>
              {stats.income_by_category && stats.income_by_category.length > 0 ? (
                <div className="space-y-3">
                  {stats.income_by_category.map((item) => (
                    <div key={item.category} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                      <div>
                        <p className="font-medium text-gray-900">{item.category}</p>
                        <p className="text-sm text-gray-600">{item.count} entry(s)</p>
                      </div>
                      <p className="text-lg font-bold text-green-600">
                        {formatCurrency(item.total_amount)}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-gray-500">
                  <p>No income entries for this period</p>
                </div>
              )}
            </div>

            {/* Expense Breakdown Table */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <ArrowDownRight className="text-red-600" size={20} />
                Expense Breakdown
              </h2>
              {expenseEntries.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="px-4 py-2 text-left text-sm font-medium text-gray-500">Date</th>
                        <th className="px-4 py-2 text-left text-sm font-medium text-gray-500">Description</th>
                        <th className="px-4 py-2 text-right text-sm font-medium text-gray-500">Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      {expenseEntries.map((expense) => (
                        <tr key={expense.id} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm text-gray-900">
                            {new Date(expense.extracted_date).toLocaleDateString('th-TH')}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-700">
                            <div>
                              <p className="font-medium">{expense.sender || expense.receiver || 'Unknown'}</p>
                              {expense.note && (
                                <p className="text-xs text-gray-500 mt-1">{expense.note}</p>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm font-semibold text-red-600 text-right">
                            {formatCurrency(parseFloat(expense.amount) || 0)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-6 text-gray-500">
                  <p>No expense entries for this period</p>
                </div>
              )}
            </div>
          </div>

          {/* Income & Salary Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Salary Section */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                  <DollarSign className="text-green-600" size={20} />
                  Salary
                </h2>
              </div>

              {incomeEntries.filter(e => e.is_salary).length > 0 ? (
                <div className="space-y-3">
                  {incomeEntries.filter(e => e.is_salary).map((entry) => (
                    <div key={entry.id} className="p-4 bg-green-50 border border-green-200 rounded-md">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-semibold text-gray-900">{entry.category}</p>
                          <p className="text-sm text-gray-600">{new Date(entry.date).toLocaleDateString('th-TH')}</p>
                          {entry.note && <p className="text-sm text-gray-500 mt-1">{entry.note}</p>}
                        </div>
                        <p className="text-lg font-bold text-green-600">
                          {formatCurrency(entry.amount)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-gray-500">
                  <p>No salary entry for this month</p>
                  <p className="text-sm mt-1">Configure salary in Settings</p>
                </div>
              )}
            </div>

            {/* Additional Income Section */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                  <TrendingUp className="text-blue-600" size={20} />
                  Additional Income
                </h2>
              </div>

              {incomeEntries.filter(e => !e.is_salary).length > 0 ? (
                <div className="space-y-3">
                  {incomeEntries.filter(e => !e.is_salary).map((entry) => (
                    <div key={entry.id} className="p-4 bg-blue-50 border border-blue-200 rounded-md">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-semibold text-gray-900">{entry.category}</p>
                          <p className="text-sm text-gray-600">{new Date(entry.date).toLocaleDateString('th-TH')}</p>
                          {entry.note && <p className="text-sm text-gray-500 mt-1">{entry.note}</p>}
                        </div>
                        <p className="text-lg font-bold text-blue-600">
                          {formatCurrency(entry.amount)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-gray-500">
                  <p>No additional income for this month</p>
                  <p className="text-sm mt-1">Go to Receipts page to add income entries</p>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
