import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Save, CheckCircle, Edit2, X } from 'lucide-react';
import { Receipt, ReceiptUpdate } from '../types/receipt';
import { receiptService } from '../services/receiptService';

export default function ReviewPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [currentReceipt, setCurrentReceipt] = useState<Receipt | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedData, setEditedData] = useState<ReceiptUpdate>({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    // Get receipts from navigation state or fetch from API
    if (location.state?.receipts) {
      setReceipts(location.state.receipts);
      setCurrentReceipt(location.state.receipts[0]);
    } else {
      // If no receipts in state, fetch from API
      fetchPendingReceipts();
    }
  }, []);

  const fetchPendingReceipts = async () => {
    try {
      const data = await receiptService.getReceipts({ status: 'pending', limit: 50 });
      if (data.length > 0) {
        setReceipts(data);
        setCurrentReceipt(data[0]);
      } else {
        // Redirect to upload if no pending receipts
        navigate('/upload');
      }
    } catch (error) {
      console.error('Failed to fetch receipts:', error);
    }
  };

  const handleNext = () => {
    if (currentIndex < receipts.length - 1) {
      const newIndex = currentIndex + 1;
      setCurrentIndex(newIndex);
      setCurrentReceipt(receipts[newIndex]);
      setIsEditing(false);
      setEditedData({});
      setSaveSuccess(false);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      const newIndex = currentIndex - 1;
      setCurrentIndex(newIndex);
      setCurrentReceipt(receipts[newIndex]);
      setIsEditing(false);
      setEditedData({});
      setSaveSuccess(false);
    }
  };

  const handleEdit = () => {
    setEditedData({
      extracted_date: currentReceipt?.extracted_date || undefined,
      extracted_time: currentReceipt?.extracted_time || undefined,
      sender: currentReceipt?.sender || undefined,
      receiver: currentReceipt?.receiver || undefined,
      amount: currentReceipt?.amount || undefined,
      note: currentReceipt?.note || undefined,
    });
    setIsEditing(true);
  };

  const handleSave = async () => {
    if (!currentReceipt) return;

    setIsSaving(true);
    try {
      const updated = await receiptService.updateReceipt(currentReceipt.id, editedData);
      setCurrentReceipt(updated);
      setReceipts(prev =>
        prev.map(r => r.id === updated.id ? updated : r)
      );
      setIsEditing(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (error) {
      console.error('Failed to update receipt:', error);
      alert('Failed to save changes. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleConfirm = async () => {
    if (!currentReceipt) return;

    try {
      await receiptService.confirmReceipt(currentReceipt.id);
      // Move to next receipt after confirming
      if (currentIndex < receipts.length - 1) {
        handleNext();
      } else {
        // All receipts reviewed, navigate to receipts list
        navigate('/receipts');
      }
    } catch (error) {
      console.error('Failed to confirm receipt:', error);
      alert('Failed to confirm receipt. Please try again.');
    }
  };

  if (!currentReceipt) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Loading receipt...</p>
      </div>
    );
  }

  const confidencePercent = currentReceipt.confidence_score
    ? Math.round(currentReceipt.confidence_score * 100)
    : 0;

  const confidenceColor = confidencePercent >= 80 ? 'green' : confidencePercent >= 60 ? 'yellow' : 'red';

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Review Receipts</h1>
        <div className="text-sm text-gray-600">
          Receipt {currentIndex + 1} of {receipts.length}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-2 mb-8">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all"
          style={{ width: `${((currentIndex + 1) / receipts.length) * 100}%` }}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Image Viewer */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">Original Image</h2>
          <div className="bg-gray-100 rounded-lg overflow-hidden">
            <img
              src={`http://localhost:8000${currentReceipt.image_path}`}
              alt={currentReceipt.filename}
              className="w-full h-auto"
            />
          </div>
          <div className="mt-4 flex items-center justify-between">
            <span className="text-sm text-gray-600">{currentReceipt.filename}</span>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Confidence:</span>
              <span className={`text-sm font-semibold text-${confidenceColor}-600`}>
                {confidencePercent}%
              </span>
            </div>
          </div>

          {/* Navigation Buttons */}
          <div className="mt-6 flex justify-between">
            <button
              onClick={handlePrevious}
              disabled={currentIndex === 0}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft size={20} />
              Previous
            </button>
            <button
              onClick={handleNext}
              disabled={currentIndex === receipts.length - 1}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
              <ChevronRight size={20} />
            </button>
          </div>
        </div>

        {/* OCR Results Form */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Extracted Information</h2>
            {!isEditing && (
              <button
                onClick={handleEdit}
                className="flex items-center gap-2 px-3 py-1 text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
              >
                <Edit2 size={16} />
                Edit
              </button>
            )}
          </div>

          {/* Success Message */}
          {saveSuccess && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <span className="text-green-700">Changes saved successfully!</span>
            </div>
          )}

          <form className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Date
              </label>
              <input
                type="date"
                value={editedData.extracted_date || currentReceipt.extracted_date || ''}
                onChange={(e) => setEditedData({ ...editedData, extracted_date: e.target.value })}
                disabled={!isEditing}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Time
              </label>
              <input
                type="time"
                value={editedData.extracted_time || currentReceipt.extracted_time || ''}
                onChange={(e) => setEditedData({ ...editedData, extracted_time: e.target.value })}
                disabled={!isEditing}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sender
              </label>
              <input
                type="text"
                value={editedData.sender || currentReceipt.sender || ''}
                onChange={(e) => setEditedData({ ...editedData, sender: e.target.value })}
                disabled={!isEditing}
                placeholder="Sender name"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Receiver
              </label>
              <input
                type="text"
                value={editedData.receiver || currentReceipt.receiver || ''}
                onChange={(e) => setEditedData({ ...editedData, receiver: e.target.value })}
                disabled={!isEditing}
                placeholder="Receiver name"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Amount (THB)
              </label>
              <input
                type="number"
                step="0.01"
                value={editedData.amount || currentReceipt.amount || ''}
                onChange={(e) => setEditedData({ ...editedData, amount: parseFloat(e.target.value) })}
                disabled={!isEditing}
                placeholder="0.00"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Note (Optional)
              </label>
              <textarea
                value={editedData.note || currentReceipt.note || ''}
                onChange={(e) => setEditedData({ ...editedData, note: e.target.value })}
                disabled={!isEditing}
                rows={3}
                placeholder="Additional notes"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
              />
            </div>

            {/* Action Buttons */}
            {isEditing && (
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setIsEditing(false);
                    setEditedData({});
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSave}
                  disabled={isSaving}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-400 flex items-center justify-center gap-2"
                >
                  <Save size={18} />
                  {isSaving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            )}
          </form>

          {/* Confirm Button */}
          {!isEditing && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <button
                onClick={handleConfirm}
                className="w-full px-4 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
              >
                <CheckCircle size={20} />
                Confirm & Continue
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
