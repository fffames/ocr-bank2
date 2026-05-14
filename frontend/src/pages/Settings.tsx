import { useState, useEffect } from 'react';
import { Settings, Save, User, Info, Trash2, Plus, RefreshCw } from 'lucide-react';
import { userService } from '../services/userService';
import { ocrCorrectionService, OCRCorrections } from '../services/ocrCorrectionService';

interface UserSettings {
  user_name: string;
  name_variations: string[];
  auto_classify: boolean;
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<UserSettings>({
    user_name: '',
    name_variations: [],
    auto_classify: true
  });
  const [ocrCorrections, setOcrCorrections] = useState<OCRCorrections>({
    corrections: {},
    count: 0
  });
  const [newWrongText, setNewWrongText] = useState('');
  const [newCorrectText, setNewCorrectText] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [variationsInput, setVariationsInput] = useState('');
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    fetchSettings();
    fetchOCRCorrections();
  }, []);

  useEffect(() => {
    setVariationsInput(settings.name_variations.join(', '));
  }, [settings.name_variations]);

  const fetchSettings = async () => {
    try {
      const data = await userService.getSettings();
      setSettings(data);
    } catch (error) {
      console.error('Failed to fetch settings:', error);
      alert('❌ Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const fetchOCRCorrections = async () => {
    try {
      const data = await ocrCorrectionService.getCorrections();
      setOcrCorrections(data);
    } catch (error) {
      console.error('Failed to fetch OCR corrections:', error);
    }
  };

  const handleAddCorrection = async () => {
    if (!newWrongText.trim() || !newCorrectText.trim()) {
      alert('Please enter both wrong and correct text');
      return;
    }

    try {
      await ocrCorrectionService.addCorrection(newWrongText, newCorrectText);
      await fetchOCRCorrections();
      setNewWrongText('');
      setNewCorrectText('');
    } catch (error) {
      console.error('Failed to add correction:', error);
      alert('❌ Failed to add correction');
    }
  };

  const handleDeleteCorrection = async (wrongText: string) => {
    if (!confirm(`Delete correction: "${wrongText}"?`)) {
      return;
    }

    try {
      await ocrCorrectionService.deleteCorrection(wrongText);
      await fetchOCRCorrections();
    } catch (error) {
      console.error('Failed to delete correction:', error);
      alert('❌ Failed to delete correction');
    }
  };

  const handleReloadCorrections = async () => {
    try {
      await ocrCorrectionService.reloadCorrections();
      await fetchOCRCorrections();
      alert('✅ Corrections reloaded from file');
    } catch (error) {
      console.error('Failed to reload corrections:', error);
      alert('❌ Failed to reload corrections');
    }
  };

  const handleSave = async () => {
    if (!settings.user_name.trim()) {
      alert('Please enter your name before saving');
      return;
    }

    setSaving(true);
    setSaveSuccess(false);
    try {
      // Parse variations from comma-separated input
      const variationsArray = variationsInput
        .split(',')
        .map(v => v.trim())
        .filter(v => v.length > 0);

      await userService.updateSettings({
        user_name: settings.user_name,
        name_variations: variationsArray,
        auto_classify: settings.auto_classify
      });

      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('❌ Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Loading settings...</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4 sm:mb-6">Settings</h1>

      <div className="max-w-2xl">
        {/* User Name Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 sm:p-6 mb-4 sm:mb-6">
          <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
            <User className="text-blue-600" size={20} />
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900">
              Your Information
            </h2>
          </div>

          <div className="space-y-3 sm:space-y-4">
            <div>
              <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1 sm:mb-2">
                Your Full Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={settings.user_name}
                onChange={(e) => setSettings({...settings, user_name: e.target.value})}
                placeholder="ชาโลม อินซ้อย"
                className="w-full px-3 sm:px-4 py-2 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="mt-1 text-xs sm:text-sm text-gray-500">
                Used to classify transactions as sending (paying) or receiving (income)
              </p>
            </div>

            <div>
              <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1 sm:mb-2">
                Name Variations (Optional)
              </label>
              <input
                type="text"
                value={variationsInput}
                onChange={(e) => setVariationsInput(e.target.value)}
                placeholder="ชาโลม, โลม, ก้อย"
                className="w-full px-3 sm:px-4 py-2 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="mt-1 text-xs sm:text-sm text-gray-500">
                Comma-separated nicknames or variations. Helps with OCR errors.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="auto_classify"
                checked={settings.auto_classify}
                onChange={(e) => setSettings({...settings, auto_classify: e.target.checked})}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="auto_classify" className="text-xs sm:text-sm font-medium text-gray-700">
                Automatically classify new receipts
              </label>
            </div>
          </div>
        </div>

        {/* OCR Corrections Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 sm:p-6 mb-4 sm:mb-6">
          <div className="flex items-center justify-between mb-3 sm:mb-4">
            <div className="flex items-center gap-2 sm:gap-3">
              <Settings className="text-purple-600" size={20} />
              <h2 className="text-lg sm:text-xl font-semibold text-gray-900">
                OCR Corrections
              </h2>
            </div>
            <div className="flex items-center gap-1 sm:gap-2">
              <span className="text-xs sm:text-sm text-gray-500">
                {ocrCorrections.count} corrections
              </span>
              <button
                onClick={handleReloadCorrections}
                className="p-1 sm:p-1.5 text-purple-600 hover:bg-purple-50 rounded transition-colors"
                title="Reload corrections from file"
              >
                <RefreshCw size={14} />
              </button>
            </div>
          </div>

          {/* Add new correction */}
          <div className="mb-4 sm:mb-6 p-3 sm:p-4 bg-gray-50 rounded-md">
            <h3 className="text-xs sm:text-sm font-medium text-gray-700 mb-2 sm:mb-3">Add New Correction</h3>
            <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 items-stretch sm:items-end">
              <div className="flex-1">
                <label className="block text-[10px] sm:text-xs font-medium text-gray-600 mb-1">
                  Wrong Text (from OCR)
                </label>
                <input
                  type="text"
                  value={newWrongText}
                  onChange={(e) => setNewWrongText(e.target.value)}
                  placeholder="เน.ย."
                  className="w-full px-2 sm:px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
              <div className="flex items-center justify-center text-gray-400 pb-0 sm:pb-2 sm:px-2">
                →
              </div>
              <div className="flex-1">
                <label className="block text-[10px] sm:text-xs font-medium text-gray-600 mb-1">
                  Correct Text
                </label>
                <input
                  type="text"
                  value={newCorrectText}
                  onChange={(e) => setNewCorrectText(e.target.value)}
                  placeholder="ม.ค."
                  className="w-full px-2 sm:px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
              <button
                onClick={handleAddCorrection}
                disabled={!newWrongText.trim() || !newCorrectText.trim()}
                className="flex items-center justify-center gap-1 sm:gap-2 px-3 sm:px-4 py-2 text-sm bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:bg-gray-400 transition-colors"
              >
                <Plus size={14} />
                <span>Add</span>
              </button>
            </div>
            <p className="mt-2 text-[10px] sm:text-xs text-gray-500">
              Map common OCR errors to correct text. Applied automatically before parsing.
              If you edit the JSON file directly, click the reload button to apply changes.
            </p>
          </div>

          {/* Existing corrections list */}
          {ocrCorrections.count > 0 ? (
            <div className="space-y-2 max-h-48 sm:max-h-64 overflow-y-auto">
              {Object.entries(ocrCorrections.corrections).map(([wrong, correct]) => (
                <div
                  key={wrong}
                  className="flex items-center justify-between p-2 sm:p-3 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-[10px] sm:text-xs font-mono truncate">
                      {wrong}
                    </span>
                    <span className="text-gray-400 flex-shrink-0">→</span>
                    <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-[10px] sm:text-xs font-mono truncate">
                      {correct}
                    </span>
                  </div>
                  <button
                    onClick={() => handleDeleteCorrection(wrong)}
                    className="p-1 sm:p-1.5 text-red-600 hover:bg-red-50 rounded transition-colors flex-shrink-0"
                    title="Delete correction"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6 sm:py-8 text-gray-500 text-xs sm:text-sm">
              No OCR corrections yet. Add one above to fix common OCR errors.
            </div>
          )}
        </div>

        {/* Info Card */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 sm:p-4 mb-4 sm:mb-6">
          <div className="flex items-start gap-2 sm:gap-3">
            <Info className="text-blue-600 mt-0.5 flex-shrink-0" size={16} />
            <div className="text-xs sm:text-sm text-blue-800">
              <strong>How it works:</strong>
              <ul className="mt-2 list-disc list-inside space-y-1">
                <li>Enter your name once in settings</li>
                <li>Upload receipts as usual</li>
                <li>System automatically classifies as:
                  <span className="ml-1 sm:ml-2 inline-flex items-center gap-1">
                    <span className="px-1.5 sm:px-2 py-0.5 bg-red-100 text-red-800 rounded text-[10px] sm:text-xs">↑ Sending</span>
                    <span className="px-1.5 sm:px-2 py-0.5 bg-green-100 text-green-800 rounded text-[10px] sm:text-xs">↓ Receiving</span>
                  </span>
                </li>
                <li>You can correct wrong classifications in Review page</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex flex-col sm:flex-row justify-end items-center gap-2 sm:gap-3">
          {saveSuccess && (
            <span className="text-green-600 text-xs sm:text-sm font-medium">
              ✓ Settings saved successfully!
            </span>
          )}
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-1 sm:gap-2 px-4 sm:px-6 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors w-full sm:w-auto"
          >
            <Save size={16} />
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
}
