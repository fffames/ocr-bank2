import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Save, CheckCircle, Edit2, RefreshCw, Grid3x3 } from 'lucide-react';
import { Receipt, ReceiptUpdate } from '../types/receipt';
import { receiptService } from '../services/receiptService';
import { API_URL } from '../services/api';
import ZoneOverlay from '../components/ZoneOverlay';

export default function ReviewPage() {
  const navigate = useNavigate();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [currentReceipt, setCurrentReceipt] = useState<Receipt | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedData, setEditedData] = useState<ReceiptUpdate>({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(currentReceipt?.detected_template || '');
  const [selectedOcrMethod, setSelectedOcrMethod] = useState<string>('auto');
  const [isReprocessing, setIsReprocessing] = useState(false);
  const [showZones, setShowZones] = useState(false);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });
  const imageRef = useRef<HTMLImageElement>(null);

  // Available templates - fetched from API
  const [templates, setTemplates] = useState<Array<{ id: string; name: string }>>([]);
  const [templatesLoading, setTemplatesLoading] = useState(true);

  useEffect(() => {
    // Always fetch fresh data from API to ensure we have latest transaction_type
    fetchPendingReceipts();
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setTemplatesLoading(true);
      const data = await receiptService.getTemplates();
      // Transform templates data to match expected format
      const transformedTemplates = data.map((tmpl: any) => ({
        id: tmpl.template_id,
        name: tmpl.bank_name || tmpl.template_id
      }));
      setTemplates(transformedTemplates);
    } catch (error) {
      console.error('Failed to fetch templates:', error);
      // Set fallback templates if API fails
      setTemplates([
        { id: 'Krungthai', name: 'Krungthai Bank' },
        { id: 'Kasikorn', name: 'Kasikorn Bank (K+)' },
        { id: 'SCB', name: 'SCB' },
        { id: 'TTB', name: 'TTB' }
      ]);
    } finally {
      setTemplatesLoading(false);
    }
  };

  const fetchPendingReceipts = async () => {
    try {
      // Fetch ALL pending receipts (backend max limit is 1000)
      const data = await receiptService.getReceipts({ status: 'pending', limit: 1000 });
      if (data.length > 0) {
        setReceipts(data);
        setCurrentReceipt(data[0]);
        setCurrentIndex(0);
      } else {
        // Redirect to receipts list if no pending receipts
        navigate('/receipts');
      }
    } catch (error) {
      console.error('Failed to fetch receipts:', error);
    }
  };

  // Update selected template when receipt changes
  useEffect(() => {
    if (currentReceipt) {
      setSelectedTemplate(currentReceipt.detected_template || '');
    }
  }, [currentReceipt]);

  // Handle image load to get dimensions
  const handleImageLoad = () => {
    if (imageRef.current) {
      setImageDimensions({
        width: imageRef.current.clientWidth,
        height: imageRef.current.clientHeight
      });
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
      extracted_date: currentReceipt?.extracted_date instanceof Date ? currentReceipt.extracted_date.toISOString().split('T')[0] : (currentReceipt?.extracted_date || undefined),
      extracted_time: currentReceipt?.extracted_time || undefined,
      sender: currentReceipt?.sender || undefined,
      receiver: currentReceipt?.receiver || undefined,
      amount: currentReceipt?.amount || undefined,
      note: currentReceipt?.note || undefined,
      transaction_type: currentReceipt?.transaction_type || undefined,
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

      // Remove confirmed receipt from list
      const updatedReceipts = receipts.filter(r => r.id !== currentReceipt.id);

      if (updatedReceipts.length > 0) {
        // Stay on review page with remaining receipts
        setReceipts(updatedReceipts);
        setCurrentReceipt(updatedReceipts[0]);
        setCurrentIndex(0);
      } else {
        // Try to fetch more pending receipts
        try {
          const moreReceipts = await receiptService.getReceipts({ status: 'pending', limit: 1000 });
          if (moreReceipts.length > 0) {
            // More pending receipts found, load them
            setReceipts(moreReceipts);
            setCurrentReceipt(moreReceipts[0]);
            setCurrentIndex(0);
          } else {
            // All receipts reviewed, navigate to receipts list
            navigate('/receipts');
          }
        } catch (error) {
          console.error('Failed to fetch more receipts:', error);
          navigate('/receipts');
        }
      }
    } catch (error) {
      console.error('Failed to confirm receipt:', error);
      alert('Failed to confirm receipt. Please try again.');
    }
  };

  const handleReprocess = async () => {
    if (!currentReceipt || !selectedTemplate) return;

    setIsReprocessing(true);
    try {
      const updated = await receiptService.reprocessReceipt(
        currentReceipt.id,
        selectedTemplate,
        selectedOcrMethod
      );
      setCurrentReceipt(updated);
      setReceipts(prev =>
        prev.map(r => r.id === updated.id ? updated : r)
      );
      setIsEditing(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (error) {
      console.error('Failed to reprocess receipt:', error);
      alert('Failed to reprocess receipt. Please try again.');
    } finally {
      setIsReprocessing(false);
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
    ? Math.round(parseFloat(String(currentReceipt.confidence_score)) * 100)
    : 0;

  const confidenceColor = confidencePercent >= 80 ? 'green' : confidencePercent >= 60 ? 'yellow' : 'red';

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Review Receipts</h1>
        <div className="text-sm text-gray-600">
          Receipt {currentIndex + 1} of {receipts.length} pending
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
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Original Image</h2>
            <button
              onClick={() => setShowZones(!showZones)}
              disabled={!currentReceipt.detected_template}
              className={`flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                showZones
                  ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50'
              }`}
              title={showZones ? 'Hide OCR zones' : 'Show OCR zones'}
            >
              <Grid3x3 size={16} />
              {showZones ? 'Hide Zones' : 'Show Zones'}
            </button>
          </div>

          {/* Image container with zone overlay */}
          <div className="relative bg-gray-100 rounded-lg overflow-hidden">
            <img
              ref={imageRef}
              src={`${API_URL}${currentReceipt.image_path}`}
              alt={currentReceipt.filename}
              className="w-full h-auto"
              onLoad={handleImageLoad}
              onError={(e) => {
                console.error('Failed to load image:', currentReceipt.image_path);
                (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect fill="%23ddd" width="400" height="300"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle"%3EImage not found%3C/text%3E%3C/svg%3E';
              }}
            />

            {/* Zone overlay */}
            {showZones && currentReceipt.detected_template && imageDimensions.width > 0 && (
              <ZoneOverlay
                templateId={currentReceipt.detected_template}
                imageWidth={imageDimensions.width}
                imageHeight={imageDimensions.height}
              />
            )}
          </div>
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">{currentReceipt.filename}</span>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Confidence:</span>
                <span className={`text-sm font-semibold text-${confidenceColor}-600`}>
                  {confidencePercent}%
                </span>
              </div>
            </div>

            {/* Template Detection Display */}
            <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-md shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-blue-900">OCR Engine</span>
                <div className="flex items-center gap-2">
                  {/* Primary OCR Engine Badge */}
                  <span className={`text-xs px-3 py-1.5 rounded-full font-medium border ${
                    currentReceipt.ocr_engine === 'gemini'
                      ? 'bg-purple-100 text-purple-800 border-purple-300'
                      : currentReceipt.ocr_engine === 'template+vlm'
                      ? 'bg-amber-100 text-amber-800 border-amber-300'
                      : 'bg-green-100 text-green-800 border-green-300'
                  }`}>
                    {currentReceipt.ocr_engine === 'gemini' && '🤖 LLM (Gemini)'}
                    {currentReceipt.ocr_engine === 'template+vlm' && '🔄 Tesseract + LLM'}
                    {(!currentReceipt.ocr_engine || currentReceipt.ocr_engine === 'template') && '📝 Tesseract'}
                  </span>
                </div>
              </div>

              {/* Processing Details */}
              <div className="space-y-2">
                {currentReceipt.detected_template ? (
                  <div className="text-sm text-blue-900">
                    <span className="font-medium">Template:</span>{' '}
                    <span className="font-semibold">
                      {templates.find(t => t.id === currentReceipt.detected_template)?.name || currentReceipt.detected_template}
                    </span>
                  </div>
                ) : (
                  <div className="text-sm text-blue-700">No template detected</div>
                )}

                {/* OCR Method Description */}
                <div className="text-xs text-blue-700">
                  {currentReceipt.ocr_engine === 'gemini' && (
                    <div className="flex items-start gap-1">
                      <span>✦</span>
                      <span>Processed by <strong>LLM (Gemini Flash Lite)</strong> only</span>
                    </div>
                  )}
                  {currentReceipt.ocr_engine === 'template+vlm' && (
                    <div className="flex items-start gap-1">
                      <span>✦</span>
                      <span>Processed by <strong>Tesseract</strong> with <strong>LLM fallback</strong> for missing fields</span>
                    </div>
                  )}
                  {(!currentReceipt.ocr_engine || currentReceipt.ocr_engine === 'template') && (
                    <div className="flex items-start gap-1">
                      <span>✦</span>
                      <span>Processed by <strong>Tesseract OCR</strong> only</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Template Selection and Reprocess */}
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Change Template & Reprocess
              </label>

              {/* Template Selection */}
              <div className="mb-3">
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Template
                </label>
                {templatesLoading ? (
                  <div className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-sm text-gray-500">
                    Loading templates...
                  </div>
                ) : (
                  <select
                    value={selectedTemplate}
                    onChange={(e) => setSelectedTemplate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
                  >
                    <option value="">Select a template...</option>
                    {templates.map(template => (
                      <option key={template.id} value={template.id}>
                        {template.name}
                      </option>
                    ))}
                  </select>
                )}
                {templates.length === 0 && !templatesLoading && (
                  <p className="mt-1 text-xs text-amber-600">
                    No templates available. Create templates in Developer Mode.
                  </p>
                )}
              </div>

              {/* OCR Method Selection */}
              <div className="mb-3">
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  OCR Method
                </label>
                <select
                  value={selectedOcrMethod}
                  onChange={(e) => setSelectedOcrMethod(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
                >
                  <option value="auto">🔄 Auto (Template + AI Fallback)</option>
                  <option value="template">🎯 Template Only (Tesseract)</option>
                  <option value="ai">🤖 AI Only (Gemini Flash Lite)</option>
                </select>
                <p className="mt-1 text-xs text-gray-500">
                  {selectedOcrMethod === 'auto' && 'Uses template OCR first, falls back to AI for missing fields'}
                  {selectedOcrMethod === 'template' && 'Uses template OCR only (faster, may miss some fields)'}
                  {selectedOcrMethod === 'ai' && 'Uses AI only (slower but more accurate)'}
                </p>
              </div>

              {/* Reprocess Button */}
              <button
                onClick={handleReprocess}
                disabled={!selectedTemplate || isReprocessing}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
              >
                <RefreshCw size={16} className={isReprocessing ? 'animate-spin' : ''} />
                {isReprocessing ? 'Processing...' : 'Reprocess OCR'}
              </button>
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
              <label className="block text-sm font-medium text-black mb-1">
                Date
              </label>
              <input
                type="date"
                value={editedData.extracted_date || (currentReceipt.extracted_date instanceof Date ? currentReceipt.extracted_date.toISOString().split('T')[0] : currentReceipt.extracted_date) || ''}
                onChange={(e) => setEditedData({ ...editedData, extracted_date: e.target.value })}
                disabled={!isEditing}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-white disabled:text-black disabled:border-gray-300 disabled:cursor-default"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Time
              </label>
              <input
                type="time"
                value={editedData.extracted_time || currentReceipt.extracted_time || ''}
                onChange={(e) => setEditedData({ ...editedData, extracted_time: e.target.value })}
                disabled={!isEditing}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-white disabled:text-black disabled:border-gray-300 disabled:cursor-default"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Sender
              </label>
              <input
                type="text"
                value={editedData.sender || currentReceipt.sender || ''}
                onChange={(e) => setEditedData({ ...editedData, sender: e.target.value })}
                disabled={!isEditing}
                placeholder="Sender name"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-white disabled:text-black disabled:border-gray-300 disabled:cursor-default"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Receiver
              </label>
              <input
                type="text"
                value={editedData.receiver || currentReceipt.receiver || ''}
                onChange={(e) => setEditedData({ ...editedData, receiver: e.target.value })}
                disabled={!isEditing}
                placeholder="Receiver name"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-white disabled:text-black disabled:border-gray-300 disabled:cursor-default"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Amount (THB)
              </label>
              <input
                type="number"
                step="0.01"
                value={editedData.amount || currentReceipt.amount || ''}
                onChange={(e) => setEditedData({ ...editedData, amount: parseFloat(e.target.value) })}
                disabled={!isEditing}
                placeholder="0.00"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-white disabled:text-black disabled:border-gray-300 disabled:cursor-default"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Note (Optional)
              </label>
              <textarea
                value={editedData.note || currentReceipt.note || ''}
                onChange={(e) => setEditedData({ ...editedData, note: e.target.value })}
                disabled={!isEditing}
                rows={3}
                placeholder="Additional notes"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-white disabled:text-black disabled:border-gray-300 disabled:cursor-default"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Transaction Type
              </label>
              <select
                value={editedData.transaction_type || currentReceipt.transaction_type || 'unknown'}
                onChange={(e) => setEditedData({ ...editedData, transaction_type: e.target.value as 'sending' | 'receiving' | 'unknown' })}
                disabled={!isEditing}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-white disabled:text-black disabled:border-gray-300 disabled:cursor-default"
              >
                <option value="sending">↑ Sending (Paying)</option>
                <option value="receiving">↓ Receiving (Income)</option>
                <option value="unknown">? Unknown</option>
              </select>
              <p className="mt-1 text-xs text-gray-500">
                {currentReceipt.transaction_confidence && `Confidence: ${currentReceipt.transaction_confidence}`}
                {currentReceipt.classification_reason && ` - ${currentReceipt.classification_reason}`}
              </p>
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
