import { useState, useEffect } from 'react';

// Helper function to format date as local date string (YYYY-MM-DD) without timezone conversion
function formatDateLocal(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}
import { Search, Trash2, Eye, Calendar, DollarSign, FileSpreadsheet, Download, Plus, X, Edit2 } from 'lucide-react';
import { Receipt } from '../types/receipt';
import { receiptService } from '../services/receiptService';
import exportService from '../services/exportService';
import { analyticsService, ManualIncome } from '../services/analyticsService';
import { API_URL } from '../services/api';
import { format } from 'date-fns';

interface ExportResult {
  success: boolean;
  rows_exported?: number;
  worksheet?: string;
  spreadsheet_url?: string;
  error?: string;
}

export default function ReceiptsListPage() {
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [yearFilter, setYearFilter] = useState<string>('all');
  const [monthFilter, setMonthFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [pageSize, setPageSize] = useState<number>(100);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [selectedReceipt, setSelectedReceipt] = useState<Receipt | null>(null);
  const [exportResult, setExportResult] = useState<ExportResult | null>(null);
  const [selectedReceiptIds, setSelectedReceiptIds] = useState<Set<number>>(new Set());
  const [bulkDeleting, setBulkDeleting] = useState(false);

  // Income management state
  const [showIncomeModal, setShowIncomeModal] = useState(false);
  const [editingIncome, setEditingIncome] = useState<ManualIncome | null>(null);
  const [incomeCategories, setIncomeCategories] = useState<Array<{id?: number; name: string}>>([]);
  const [incomeForm, setIncomeForm] = useState<ManualIncome>({
    amount: 0,
    category: 'Salary',
    income_date: new Date().toISOString().split('T')[0],
    note: ''
  });

  // Receipt editing state
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingReceipt, setEditingReceipt] = useState<Receipt | null>(null);
  const [editForm, setEditForm] = useState({
    sender: '',
    receiver: '',
    amount: '',
    extracted_date: '',
    extracted_time: '',
    note: '',
    transaction_type: '',
    income_category: ''
  });

  useEffect(() => {
    fetchReceipts();
    // Clear selections when filters change
    setSelectedReceiptIds(new Set());
  }, [statusFilter, yearFilter, monthFilter, typeFilter, pageSize, currentPage]);

  // Reset to page 1 when filters or page size changes
  useEffect(() => {
    setCurrentPage(1);
  }, [statusFilter, yearFilter, monthFilter, typeFilter, pageSize]);

  // Debug logging (without filteredReceipts to avoid initialization issues)
  useEffect(() => {
    console.log('🔄 Component state updated:', {
      loading,
      receiptsCount: receipts.length,
      searchTerm,
      statusFilter,
      yearFilter,
      monthFilter,
      typeFilter
    });
  }, [loading, receipts, searchTerm, statusFilter, yearFilter, monthFilter, typeFilter]);

  const fetchReceipts = async () => {
    setLoading(true);
    try {
      console.log('🔍 Fetching receipts...');

      // For client-side pagination, fetch all matching data
      // Backend has a max limit of 1000 per request
      const params: any = {
        limit: 1000, // Backend maximum limit
      };

      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }

      if (typeFilter !== 'all') {
        params.transaction_type = typeFilter;
      }

      // Handle year/month filtering
      if (yearFilter !== 'all' || monthFilter !== 'all') {
        const year = yearFilter !== 'all' ? parseInt(yearFilter) : new Date().getFullYear();
        const month = monthFilter !== 'all' ? parseInt(monthFilter) - 1 : 0; // JavaScript months are 0-indexed

        if (monthFilter !== 'all') {
          // Specific month: create date range for that month
          const startDate = new Date(year, month, 1);
          const endDate = new Date(year, month + 1, 0); // Last day of month

          params.date_from = startDate.toISOString().split('T')[0];
          params.date_to = endDate.toISOString().split('T')[0];
        } else {
          // Entire year
          const startDate = new Date(year, 0, 1);
          const endDate = new Date(year, 11, 31);

          params.date_from = startDate.toISOString().split('T')[0];
          params.date_to = endDate.toISOString().split('T')[0];
        }
      }

      console.log('📤 Fetching with params:', params);
      const data = await receiptService.getReceipts(params);
      console.log(`✅ Fetched ${data.length} receipts`);
      setReceipts(data);
    } catch (error) {
      console.error('❌ Error fetching receipts:', error);
      setReceipts([]);
    } finally {
      setLoading(false);
    }
  };


  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this receipt?')) return;

    try {
      await receiptService.deleteReceipt(id);
      setReceipts(prev => prev.filter(r => r.id !== id));
      if (selectedReceipt?.id === id) {
        setSelectedReceipt(null);
      }
    } catch (error) {
      console.error('Failed to delete receipt:', error);
      alert('Failed to delete receipt. Please try again.');
    }
  };

  // Selection and bulk delete functions
  const handleToggleSelectAll = () => {
    // Check if all current page items are selected
    const currentPageIds = new Set(paginatedReceipts.map(r => r.id));
    const allCurrentPageSelected = paginatedReceipts.every(r => selectedReceiptIds.has(r.id));

    if (allCurrentPageSelected) {
      // Deselect all items on current page
      const newSelection = new Set(selectedReceiptIds);
      currentPageIds.forEach(id => newSelection.delete(id));
      setSelectedReceiptIds(newSelection);
    } else {
      // Select all items on current page
      const newSelection = new Set(selectedReceiptIds);
      paginatedReceipts.forEach(r => newSelection.add(r.id));
      setSelectedReceiptIds(newSelection);
    }
  };

  const handleToggleSelect = (id: number) => {
    const newSelected = new Set(selectedReceiptIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedReceiptIds(newSelected);
  };

  const handleBulkDelete = async () => {
    if (selectedReceiptIds.size === 0) return;

    const count = selectedReceiptIds.size;
    if (!confirm(`Are you sure you want to delete ${count} receipt${count > 1 ? 's' : ''}?`)) return;

    setBulkDeleting(true);
    try {
      // Delete all selected receipts
      const deletePromises = Array.from(selectedReceiptIds).map(id =>
        receiptService.deleteReceipt(id)
      );
      await Promise.all(deletePromises);

      // Update state
      setReceipts(prev => prev.filter(r => !selectedReceiptIds.has(r.id)));
      setSelectedReceiptIds(new Set());
      setSelectedReceipt(null);

      alert(`✅ Successfully deleted ${count} receipt${count > 1 ? 's' : ''}`);
    } catch (error) {
      console.error('Failed to delete receipts:', error);
      alert(`Failed to delete some receipts. Please try again.`);
    } finally {
      setBulkDeleting(false);
    }
  };

  // Income management functions
  const fetchIncomeCategories = async () => {
    try {
      const categories = await analyticsService.getIncomeCategories();
      console.log('📁 Income categories loaded:', categories);

      // If no categories exist, show default options
      if (categories.length === 0) {
        console.log('No categories found, using defaults');
        setIncomeCategories([
          { name: 'Salary' },
          { name: 'Freelance' },
          { name: 'Bonus' },
          { name: 'Investment Return' },
          { name: 'Commission' },
          { name: 'Gift' },
          { name: 'Refund' },
          { name: 'Rental Income' },
          { name: 'Other Income' }
        ]);
      } else {
        setIncomeCategories(categories);
      }
    } catch (error) {
      console.error('Failed to load income categories:', error);
      // If API fails, use default categories
      setIncomeCategories([
        { name: 'Salary' },
        { name: 'Freelance' },
        { name: 'Bonus' },
        { name: 'Investment Return' },
        { name: 'Commission' },
        { name: 'Gift' },
        { name: 'Refund' },
        { name: 'Rental Income' },
        { name: 'Other Income' }
      ]);
    }
  };

  const handleOpenIncomeModal = async () => {
    setEditingIncome(null);
    await fetchIncomeCategories();

    // Set first category as default if available
    const defaultCategory = incomeCategories.length > 0 ? incomeCategories[0].name : 'Other Income';
    setIncomeForm({
      amount: 0,
      category: defaultCategory,
      income_date: new Date().toISOString().split('T')[0],
      note: ''
    });
    setShowIncomeModal(true);
  };

  const handleCloseIncomeModal = () => {
    setShowIncomeModal(false);
    setEditingIncome(null);
    setIncomeForm({
      amount: 0,
      category: 'Other Income',
      income_date: new Date().toISOString().split('T')[0],
      note: ''
    });
  };

  const handleSaveIncome = async () => {
    if (incomeForm.amount <= 0) {
      alert('Please enter a valid amount');
      return;
    }

    try {
      if (editingIncome) {
        // Update existing income - not implemented in backend yet
        alert('Edit functionality coming soon');
      } else {
        // Create new income
        await analyticsService.createManualIncome(incomeForm);
        alert('✅ Income entry added successfully');
      }

      handleCloseIncomeModal();
      fetchReceipts(); // Reload to show new entry
    } catch (error: any) {
      console.error('Failed to save income:', error);
      alert(`Failed to save income: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Receipt editing functions
  const handleEditReceipt = async (receipt: Receipt) => {
    // Load income categories if not already loaded
    if (incomeCategories.length === 0) {
      await fetchIncomeCategories();
    }

    setEditingReceipt(receipt);
    setEditForm({
      sender: receipt.sender || '',
      receiver: receipt.receiver || '',
      amount: receipt.amount ? String(receipt.amount) : '',
      extracted_date: receipt.extracted_date instanceof Date ? receipt.extracted_date.toISOString().split('T')[0] : (receipt.extracted_date || ''),
      extracted_time: receipt.extracted_time || '',
      note: receipt.note || '',
      transaction_type: receipt.transaction_type || 'unknown',
      income_category: receipt.income_category || ''
    });
    setShowEditModal(true);
  };

  const handleCloseEditModal = () => {
    setShowEditModal(false);
    setEditingReceipt(null);
    setEditForm({
      sender: '',
      receiver: '',
      amount: '',
      extracted_date: '',
      extracted_time: '',
      note: '',
      transaction_type: '',
      income_category: ''
    });
  };

  const handleSaveReceiptEdit = async () => {
    if (!editingReceipt) return;

    try {
      const updateData: any = {};
      if (editForm.sender !== editingReceipt.sender) updateData.sender = editForm.sender;
      if (editForm.receiver !== editingReceipt.receiver) updateData.receiver = editForm.receiver;
      if (editForm.amount && parseFloat(editForm.amount) !== parseFloat(String(editingReceipt.amount || 0))) {
        updateData.amount = parseFloat(editForm.amount);
      }
      if (editForm.extracted_date && editForm.extracted_date !== editingReceipt.extracted_date) {
        updateData.extracted_date = editForm.extracted_date;
      }
      if (editForm.extracted_time && editForm.extracted_time !== editingReceipt.extracted_time) {
        updateData.extracted_time = editForm.extracted_time;
      }
      if (editForm.note !== editingReceipt.note) updateData.note = editForm.note;
      if (editForm.transaction_type && editForm.transaction_type !== editingReceipt.transaction_type) {
        updateData.transaction_type = editForm.transaction_type;
      }
      if (editForm.income_category && editForm.income_category !== editingReceipt.income_category) {
        updateData.income_category = editForm.income_category;
      }

      // Auto-change status from 'pending' to 'confirmed' when editing
      if (editingReceipt.status === 'pending') {
        updateData.status = 'confirmed';
      }

      await receiptService.updateReceipt(editingReceipt.id, updateData);
      alert('✅ Receipt updated successfully');
      handleCloseEditModal();
      fetchReceipts();
    } catch (error: any) {
      console.error('Failed to update receipt:', error);
      alert(`Failed to update receipt: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleExportAll = async () => {
    try {
      // Export all receipts (no filters)
      await exportService.exportToExcel({});
      alert('✅ Excel download started!');
    } catch (error: any) {
      console.error('Export error:', error);
      alert('❌ Export failed. Please try again.');
    }
  };

  const handleExportFiltered = async () => {
    try {
      if (filteredReceipts.length === 0) {
        alert('No receipts to export');
        return;
      }

      // Build filters from current UI state
      const filters: any = {};

      // Add status filter
      if (statusFilter !== 'all') {
        filters.status = statusFilter;
      }

      // Add transaction type filter
      if (typeFilter !== 'all') {
        filters.transaction_type = typeFilter;
      }

      // Add date range filter from year/month
      if (yearFilter !== 'all') {
        const year = parseInt(yearFilter);
        if (monthFilter !== 'all') {
          // Specific month
          const month = parseInt(monthFilter);
          const startDate = new Date(year, month - 1, 1);
          const endDate = new Date(year, month, 0); // Last day of month
          filters.date_from = formatDateLocal(startDate);
          filters.date_to = formatDateLocal(endDate);
        } else {
          // Entire year
          filters.date_from = `${year}-01-01`;
          filters.date_to = `${year}-12-31`;
        }
      } else if (monthFilter !== 'all') {
        // Month selected but no year - use current year
        const currentYear = new Date().getFullYear();
        const month = parseInt(monthFilter);
        const startDate = new Date(currentYear, month - 1, 1);
        const endDate = new Date(currentYear, month, 0); // Last day of month
        filters.date_from = formatDateLocal(startDate);
        filters.date_to = formatDateLocal(endDate);
      }

      console.log('📤 Exporting with filters:', filters);
      console.log('📊 Current filter state:', { statusFilter, typeFilter, yearFilter, monthFilter });

      await exportService.exportToExcel(filters);
      alert('✅ Excel download started!');
    } catch (error: any) {
      console.error('Export error:', error);
      alert('❌ Export failed. Please try again.');
    }
  };

  const handleExportSummary = async () => {
    try {
      await exportService.exportToExcel({});
      alert('✅ Excel download started!');
    } catch (error: any) {
      console.error('Export error:', error);
      alert('❌ Export failed. Please try again.');
    }
  };

  const filteredReceipts = receipts.filter(receipt =>
    receipt.sender?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    receipt.receiver?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    receipt.note?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Pagination logic
  const totalPages = pageSize === -1 ? 1 : Math.ceil(filteredReceipts.length / pageSize);
  const startIndex = pageSize === -1 ? 0 : (currentPage - 1) * pageSize;
  const endIndex = pageSize === -1 ? filteredReceipts.length : startIndex + pageSize;
  const paginatedReceipts = filteredReceipts.slice(startIndex, endIndex);

  // Ensure currentPage is valid
  useEffect(() => {
    if (currentPage > totalPages && totalPages > 0) {
      setCurrentPage(totalPages);
    }
  }, [totalPages, currentPage]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'bg-green-100 text-green-800';
      case 'reviewed':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Receipts</h1>

      {/* Search and Filter */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex flex-col gap-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="Search by sender, receiver, or note..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="reviewed">Reviewed</option>
              <option value="confirmed">Confirmed</option>
            </select>
          </div>

          {/* Additional Filters */}
          <div className="flex flex-col md:flex-row gap-4 items-center">
            {/* Year Filter */}
            <select
              value={yearFilter}
              onChange={(e) => setYearFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Years</option>
              <option value="2026">2026</option>
              <option value="2025">2025</option>
              <option value="2024">2024</option>
              <option value="2023">2023</option>
            </select>

            {/* Month Filter */}
            <select
              value={monthFilter}
              onChange={(e) => setMonthFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Months</option>
              <option value="1">January</option>
              <option value="2">February</option>
              <option value="3">March</option>
              <option value="4">April</option>
              <option value="5">May</option>
              <option value="6">June</option>
              <option value="7">July</option>
              <option value="8">August</option>
              <option value="9">September</option>
              <option value="10">October</option>
              <option value="11">November</option>
              <option value="12">December</option>
            </select>

            {/* Transaction Type Filter */}
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Types</option>
              <option value="sending">↑ Sending (Expenses)</option>
              <option value="receiving">↓ Receiving (Income)</option>
              <option value="unknown">? Unknown</option>
            </select>

            {/* Page Size Selector */}
            <select
              value={pageSize}
              onChange={(e) => setPageSize(e.target.value === 'all' ? -1 : parseInt(e.target.value))}
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 font-medium"
            >
              <option value={20}>20 rows</option>
              <option value={50}>50 rows</option>
              <option value={100}>100 rows</option>
              <option value="all">All rows</option>
            </select>

            {/* Clear Filters Button */}
            {(statusFilter !== 'all' || yearFilter !== 'all' || monthFilter !== 'all' || typeFilter !== 'all') && (
              <button
                onClick={() => {
                  setStatusFilter('all');
                  setYearFilter('all');
                  setMonthFilter('all');
                  setTypeFilter('all');
                }}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
              >
                Clear Filters
              </button>
            )}
          </div>

          {/* Export and Action Buttons */}
          <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-200">
            <button
              onClick={handleOpenIncomeModal}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 transition-colors"
            >
              <Plus size={18} />
              Add Income
            </button>
            {selectedReceiptIds.size > 0 && (
              <button
                onClick={handleBulkDelete}
                disabled={bulkDeleting}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                <Trash2 size={18} />
                Delete Selected ({selectedReceiptIds.size})
              </button>
            )}
            <button
              onClick={() => handleExportAll()}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
            >
              <FileSpreadsheet size={18} />
              Export All to Sheets
            </button>
            <button
              onClick={() => handleExportFiltered()}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <Download size={18} />
              Export Filtered Results
            </button>
            <button
              onClick={() => handleExportSummary()}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
            >
              <FileSpreadsheet size={18} />
              Export Summary
            </button>
          </div>
        </div>
      </div>

      {/* Receipts Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-600">Loading receipts...</p>
          </div>
        ) : filteredReceipts.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600">No receipts found</p>
          </div>
        ) : (
          <>
            {/* Results count with pagination info */}
            <div className="mb-4 flex items-center justify-between text-sm text-gray-600">
              <div>
                Showing <span className="font-semibold text-gray-900">{startIndex + 1}</span>
                to <span className="font-semibold text-gray-900">{Math.min(endIndex, filteredReceipts.length)}</span>
                of <span className="font-semibold text-gray-900">{filteredReceipts.length}</span> receipts
                {pageSize !== -1 && (
                  <span className="ml-2">(page {currentPage} of {totalPages})</span>
                )}
              </div>
            </div>

            <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-12">
                    <input
                      type="checkbox"
                      checked={paginatedReceipts.length > 0 && paginatedReceipts.every(r => selectedReceiptIds.has(r.id))}
                      onChange={handleToggleSelectAll}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Sender
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Receiver
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {paginatedReceipts.map((receipt) => (
                  <tr key={receipt.id} className={`hover:bg-gray-50 ${selectedReceiptIds.has(receipt.id) ? 'bg-blue-50' : ''}`}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={selectedReceiptIds.has(receipt.id)}
                        onChange={() => handleToggleSelect(receipt.id)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {receipt.extracted_date ? (
                        <div className="flex items-center gap-2">
                          <Calendar size={16} className="text-gray-400" />
                          {format(receipt.extracted_date instanceof Date ? receipt.extracted_date : new Date(receipt.extracted_date), 'MMM dd, yyyy')}
                        </div>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {receipt.sender || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {receipt.receiver || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {receipt.amount ? (
                        <div className="flex items-center gap-2">
                          <DollarSign size={16} className="text-gray-400" />
                          ฿{typeof receipt.amount === 'number'
                            ? receipt.amount.toFixed(2)
                            : parseFloat(receipt.amount).toFixed(2)}
                        </div>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex flex-col gap-1">
                        {/* Transaction Type Badge */}
                        {receipt.transaction_type === 'receiving' ? (
                          // Income - show category
                          receipt.income_category ? (
                            <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full ${
                              receipt.is_salary
                                ? 'bg-emerald-100 text-emerald-800 border-2 border-emerald-200'
                                : 'bg-green-100 text-green-800'
                            }`}>
                              {receipt.is_salary && '💰 '}
                              {receipt.income_category}
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">
                              ↓ Income
                            </span>
                          )
                        ) : receipt.transaction_type === 'sending' ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">
                            ↑ Sending
                          </span>
                        ) : receipt.transaction_type === 'unknown' ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">
                            ? Unknown
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}

                        {/* OCR Engine Badge */}
                        {receipt.ocr_engine && (
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium rounded-full border ${
                            receipt.ocr_engine === 'gemini'
                              ? 'bg-purple-50 text-purple-700 border-purple-200'
                              : receipt.ocr_engine === 'template+vlm'
                              ? 'bg-amber-50 text-amber-700 border-amber-200'
                              : 'bg-green-50 text-green-700 border-green-200'
                          }`}>
                            {receipt.ocr_engine === 'gemini' && '🤖 LLM'}
                            {receipt.ocr_engine === 'template+vlm' && '📝+🤖'}
                            {receipt.ocr_engine === 'template' && '📝 Tesseract'}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(receipt.status)}`}>
                        {receipt.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setSelectedReceipt(receipt)}
                          className="text-blue-600 hover:text-blue-800"
                          title="View details"
                        >
                          <Eye size={18} />
                        </button>
                        <button
                          onClick={() => handleEditReceipt(receipt)}
                          className="text-amber-600 hover:text-amber-800"
                          title="Edit receipt"
                        >
                          <Edit2 size={18} />
                        </button>
                        <button
                          onClick={() => handleDelete(receipt.id)}
                          className="text-red-600 hover:text-red-800"
                          title="Delete"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination Controls */}
            {pageSize !== -1 && totalPages > 1 && (
              <div className="flex items-center justify-between px-6 py-4 bg-gray-50 border-t border-gray-200">
                <div className="text-sm text-gray-600">
                  Page <span className="font-semibold">{currentPage}</span> of <span className="font-semibold">{totalPages}</span>
                </div>

                <div className="flex items-center gap-2">
                  {/* Previous Button */}
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                    className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>

                  {/* Page Numbers */}
                  <div className="flex items-center gap-1">
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      let pageNum;

                      // Show pages around current page
                      if (totalPages <= 5) {
                        pageNum = i + 1;
                      } else if (currentPage <= 3) {
                        pageNum = i + 1;
                      } else if (currentPage >= totalPages - 2) {
                        pageNum = totalPages - 4 + i;
                      } else {
                        pageNum = currentPage - 2 + i;
                      }

                      return (
                        <button
                          key={pageNum}
                          onClick={() => setCurrentPage(pageNum)}
                          className={`px-3 py-1 text-sm border rounded-md ${
                            currentPage === pageNum
                              ? 'bg-blue-600 text-white border-blue-600'
                              : 'border-gray-300 hover:bg-gray-100'
                          }`}
                        >
                          {pageNum}
                        </button>
                      );
                    })}
                  </div>

                  {/* Next Button */}
                  <button
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
          </>
        )}
      </div>

      {/* Receipt Detail Modal */}
      {selectedReceipt && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-gray-900">Receipt Details</h2>
                <button
                  onClick={() => setSelectedReceipt(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Image */}
                <div>
                  <h3 className="text-lg font-semibold mb-2">Original Image</h3>
                  <img
                    src={`${API_URL}${selectedReceipt.image_path}`}
                    alt={selectedReceipt.filename}
                    className="w-full rounded-lg border border-gray-200"
                    onError={(e) => {
                      console.error('Failed to load image:', selectedReceipt.image_path);
                      (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect fill="%23ddd" width="400" height="300"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle"%3EImage not found%3C/text%3E%3C/svg%3E';
                    }}
                  />
                </div>

                {/* Details */}
                <div>
                  <h3 className="text-lg font-semibold mb-4">Extracted Information</h3>
                  <dl className="space-y-3">
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Filename</dt>
                      <dd className="text-sm text-gray-900">{selectedReceipt.filename}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Date</dt>
                      <dd className="text-sm text-gray-900">
                        {selectedReceipt.extracted_date ? format(selectedReceipt.extracted_date instanceof Date ? selectedReceipt.extracted_date : new Date(selectedReceipt.extracted_date), 'MMM dd, yyyy') : '-'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Time</dt>
                      <dd className="text-sm text-gray-900">{selectedReceipt.extracted_time || '-'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Sender</dt>
                      <dd className="text-sm text-gray-900">{selectedReceipt.sender || '-'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Receiver</dt>
                      <dd className="text-sm text-gray-900">{selectedReceipt.receiver || '-'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Amount</dt>
                      <dd className="text-sm text-gray-900">
                        {selectedReceipt.amount ? `฿${
                          typeof selectedReceipt.amount === 'number'
                            ? selectedReceipt.amount.toFixed(2)
                            : parseFloat(selectedReceipt.amount).toFixed(2)
                        }` : '-'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Note</dt>
                      <dd className="text-sm text-gray-900">{selectedReceipt.note || '-'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Confidence</dt>
                      <dd className="text-sm text-gray-900">
                        {selectedReceipt.confidence_score
                          ? `${Math.round(
                              typeof selectedReceipt.confidence_score === 'number'
                                ? selectedReceipt.confidence_score * 100
                                : parseFloat(selectedReceipt.confidence_score) * 100
                            )}%`
                          : '-'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Status</dt>
                      <dd className="text-sm">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(selectedReceipt.status)}`}>
                          {selectedReceipt.status}
                        </span>
                      </dd>
                    </div>
                  </dl>
                </div>
              </div>

              {/* OCR Raw Text */}
              {selectedReceipt.ocr_raw_text && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold mb-2">Raw OCR Text</h3>
                  <pre className="bg-gray-50 p-4 rounded-lg text-sm text-gray-700 overflow-x-auto">
                    {selectedReceipt.ocr_raw_text}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Income Modal */}
      {showIncomeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                {editingIncome ? 'Edit Income' : 'Add Income Entry'}
              </h2>
              <button
                onClick={handleCloseIncomeModal}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Amount (THB) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  value={incomeForm.amount || ''}
                  onChange={(e) => setIncomeForm({...incomeForm, amount: parseFloat(e.target.value) || 0})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="3000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Category <span className="text-red-500">*</span>
                </label>
                <select
                  value={incomeForm.category}
                  onChange={(e) => setIncomeForm({...incomeForm, category: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  {incomeCategories.length > 0 ? (
                    incomeCategories.map((cat) => (
                      <option key={cat.id || cat.name} value={cat.name}>
                        {cat.name}
                      </option>
                    ))
                  ) : (
                    <option value="Other Income">Other Income</option>
                  )}
                </select>
                <p className="mt-1 text-sm text-gray-500">
                  Select the type of income
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Date <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  value={incomeForm.income_date}
                  onChange={(e) => setIncomeForm({...incomeForm, income_date: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Note (optional)
                </label>
                <input
                  type="text"
                  value={incomeForm.note}
                  onChange={(e) => setIncomeForm({...incomeForm, note: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Additional work, side project, etc."
                />
              </div>
            </div>

            <div className="flex gap-3 p-6 border-t border-gray-200">
              <button
                onClick={handleSaveIncome}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                {editingIncome ? 'Update' : 'Add'} Income
              </button>
              <button
                onClick={handleCloseIncomeModal}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Receipt Modal */}
      {showEditModal && editingReceipt && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-200 sticky top-0 bg-white">
              <h2 className="text-xl font-semibold text-gray-900">
                Edit Receipt {editingReceipt.is_salary ? '(Salary)' : ''} {editingReceipt.is_manual_income ? '(Manual Income)' : ''}
              </h2>
              <button
                onClick={handleCloseEditModal}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <div className="p-6 space-y-4">
              {/* Amount */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Amount (THB) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={editForm.amount}
                  onChange={(e) => setEditForm({...editForm, amount: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="1000.00"
                />
              </div>

              {/* Date and Time */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Date <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    value={editForm.extracted_date}
                    onChange={(e) => setEditForm({...editForm, extracted_date: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Time
                  </label>
                  <input
                    type="time"
                    value={editForm.extracted_time}
                    onChange={(e) => setEditForm({...editForm, extracted_time: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              {/* Sender and Receiver */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Sender
                  </label>
                  <input
                    type="text"
                    value={editForm.sender}
                    onChange={(e) => setEditForm({...editForm, sender: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Sender name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Receiver
                  </label>
                  <input
                    type="text"
                    value={editForm.receiver}
                    onChange={(e) => setEditForm({...editForm, receiver: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Receiver name"
                  />
                </div>
              </div>

              {/* Transaction Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Transaction Type
                </label>
                <select
                  value={editForm.transaction_type}
                  onChange={(e) => setEditForm({...editForm, transaction_type: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="sending">↑ Sending (Expense)</option>
                  <option value="receiving">↓ Receiving (Income)</option>
                  <option value="unknown">? Unknown</option>
                </select>
              </div>

              {/* Income Category (only for receiving transactions) */}
              {(editForm.transaction_type === 'receiving' || editingReceipt.income_category) && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Income Category
                  </label>
                  <select
                    value={editForm.income_category}
                    onChange={(e) => setEditForm({...editForm, income_category: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">No category</option>
                    {incomeCategories.map((cat) => (
                      <option key={cat.id || cat.name} value={cat.name}>
                        {cat.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Note */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Note
                </label>
                <textarea
                  value={editForm.note}
                  onChange={(e) => setEditForm({...editForm, note: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  rows={3}
                  placeholder="Add any notes..."
                />
              </div>
            </div>

            <div className="flex gap-3 p-6 border-t border-gray-200">
              <button
                onClick={handleSaveReceiptEdit}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Save Changes
              </button>
              <button
                onClick={handleCloseEditModal}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Export Success Modal */}
      {exportResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-gray-900">✅ Export Successful!</h2>
              <button
                onClick={() => setExportResult(null)}
                className="text-gray-400 hover:text-gray-600 text-3xl"
              >
                ×
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-600 mb-2">
                  {exportResult.rows_exported
                    ? `Exported ${exportResult.rows_exported} receipts`
                    : 'Exported summary'}
                </p>
                <p className="text-sm text-gray-600">
                  Worksheet: <span className="font-mono font-semibold">{exportResult.worksheet}</span>
                </p>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-sm font-medium text-green-900 mb-3">
                  📊 Open your Google Sheets spreadsheet:
                </p>
                <a
                  href={exportResult.spreadsheet_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block w-full text-center px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
                >
                  Open Spreadsheet
                </a>
              </div>

              <div className="text-xs text-gray-500">
                <p className="mb-1">💡 Tip: Right-click the button and select "Copy link address" if you want to share it.</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
