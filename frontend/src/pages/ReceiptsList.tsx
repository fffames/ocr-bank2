import { useState, useEffect } from 'react';
import { Search, Trash2, Eye, Calendar, User, DollarSign } from 'lucide-react';
import { Receipt } from '../types/receipt';
import { receiptService } from '../services/receiptService';
import { format } from 'date-fns';

export default function ReceiptsListPage() {
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedReceipt, setSelectedReceipt] = useState<Receipt | null>(null);

  useEffect(() => {
    fetchReceipts();
  }, [statusFilter]);

  const fetchReceipts = async () => {
    setLoading(true);
    try {
      const params: any = {
        limit: 100,
      };
      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }
      const data = await receiptService.getReceipts(params);
      setReceipts(data);
    } catch (error) {
      console.error('Failed to fetch receipts:', error);
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

  const filteredReceipts = receipts.filter(receipt =>
    receipt.sender?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    receipt.receiver?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    receipt.note?.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
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
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredReceipts.map((receipt) => (
                  <tr key={receipt.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {receipt.extracted_date ? (
                        <div className="flex items-center gap-2">
                          <Calendar size={16} className="text-gray-400" />
                          {format(new Date(receipt.extracted_date), 'MMM dd, yyyy')}
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
                          ฿{receipt.amount.toFixed(2)}
                        </div>
                      ) : (
                        '-'
                      )}
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
          </div>
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
                    src={`http://localhost:8000${selectedReceipt.image_path}`}
                    alt={selectedReceipt.filename}
                    className="w-full rounded-lg border border-gray-200"
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
                        {selectedReceipt.extracted_date ? format(new Date(selectedReceipt.extracted_date), 'MMM dd, yyyy') : '-'}
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
                        {selectedReceipt.amount ? `฿${selectedReceipt.amount.toFixed(2)}` : '-'}
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
                          ? `${Math.round(selectedReceipt.confidence_score * 100)}%`
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
    </div>
  );
}
