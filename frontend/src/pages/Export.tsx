import { useState } from 'react';
import { Download, Filter } from 'lucide-react';
import exportService from '../services/exportService';

interface ExportFilters {
  date_from?: string;
  date_to?: string;
  transaction_type?: 'sending' | 'receiving' | 'all';
  status?: 'pending' | 'reviewed' | 'confirmed' | 'all';
}

export default function ExportPage() {
  const [filters, setFilters] = useState<ExportFilters>({
    transaction_type: 'all',
    status: 'all'
  });
  const [preview] = useState<{payments: number; income: number} | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      await exportService.exportToExcel(filters);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export receipts. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Export Receipts</h1>
        <p className="text-gray-600 mt-2">
          Download your receipts as an Excel file with filters
        </p>
      </div>

      {/* Filter Section */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Filter size={20} />
          Filters
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Date Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={filters.date_from || ''}
              onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              type="date"
              value={filters.date_to || ''}
              onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Transaction Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Transaction Type
            </label>
            <select
              value={filters.transaction_type}
              onChange={(e) => setFilters({ ...filters, transaction_type: e.target.value as any })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Transactions</option>
              <option value="sending">Payments (Sending)</option>
              <option value="receiving">Income (Receiving)</option>
            </select>
          </div>

          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value as any })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="reviewed">Reviewed</option>
              <option value="confirmed">Confirmed</option>
            </select>
          </div>
        </div>

        {/* Preview Section */}
        {preview && (
          <div className="mt-4 p-4 bg-gray-50 rounded-md">
            <p className="text-sm text-gray-600">
              Matching receipts: <strong>{preview.payments}</strong> payments, <strong>{preview.income}</strong> income
            </p>
          </div>
        )}
      </div>

      {/* Export Button */}
      <div className="bg-white rounded-lg shadow p-6">
        <button
          onClick={handleExport}
          disabled={isExporting}
          className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
        >
          <Download size={20} />
          {isExporting ? 'Generating Excel...' : 'Download Excel'}
        </button>
      </div>
    </div>
  );
}
