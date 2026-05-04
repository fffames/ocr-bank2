import { useState, useEffect } from 'react';
import { Settings, Save, User, Info, DollarSign, Trash2, Plus, RefreshCw } from 'lucide-react';
import { userService } from '../services/userService';
import { analyticsService, SalaryConfig } from '../services/analyticsService';
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
  const [salaryConfig, setSalaryConfig] = useState<SalaryConfig>({
    default_salary_amount: 0,
    salary_day_of_month: 1,
    salary_category: 'Salary'
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
  const [salarySaving, setSalarySaving] = useState(false);
  const [salarySaveSuccess, setSalarySaveSuccess] = useState(false);
  const [salaryUpdatedMessage, setSalaryUpdatedMessage] = useState('');

  useEffect(() => {
    fetchSettings();
    fetchSalaryConfig();
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

  const fetchSalaryConfig = async () => {
    try {
      const data = await analyticsService.getSalaryConfig();
      setSalaryConfig(data);
    } catch (error) {
      console.error('Failed to fetch salary config:', error);
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

  const handleSaveSalary = async () => {
    if (salaryConfig.default_salary_amount <= 0) {
      alert('Please enter a valid salary amount');
      return;
    }

    if (salaryConfig.salary_day_of_month < 1 || salaryConfig.salary_day_of_month > 31) {
      alert('Salary day must be between 1 and 31');
      return;
    }

    setSalarySaving(true);
    setSalarySaveSuccess(false);
    setSalaryUpdatedMessage('');
    try {
      const response = await analyticsService.updateSalaryConfig(salaryConfig);

      // Check if current month's salary was updated
      if ('updated_current_month_salary' in response) {
        const updated = response.updated_current_month_salary as { amount: number; date: string };
        setSalaryUpdatedMessage(
          `✅ Current month's salary updated to ${new Intl.NumberFormat('th-TH', {
            style: 'currency',
            currency: 'THB'
          }).format(updated.amount)}`
        );
      }

      setSalarySaveSuccess(true);
      setTimeout(() => {
        setSalarySaveSuccess(false);
        setSalaryUpdatedMessage('');
      }, 5000);
    } catch (error) {
      console.error('Failed to save salary config:', error);
      alert('❌ Failed to save salary configuration');
    } finally {
      setSalarySaving(false);
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
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Settings</h1>

      <div className="max-w-2xl">
        {/* User Name Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <User className="text-blue-600" size={24} />
            <h2 className="text-xl font-semibold text-gray-900">
              Your Information
            </h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Full Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={settings.user_name}
                onChange={(e) => setSettings({...settings, user_name: e.target.value})}
                placeholder="ชาโลม อินซ้อย"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="mt-1 text-sm text-gray-500">
                Used to classify transactions as sending (paying) or receiving (income)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Name Variations (Optional)
              </label>
              <input
                type="text"
                value={variationsInput}
                onChange={(e) => setVariationsInput(e.target.value)}
                placeholder="ชาโลม, โลม, ก้อย"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="mt-1 text-sm text-gray-500">
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
              <label htmlFor="auto_classify" className="text-sm font-medium text-gray-700">
                Automatically classify new receipts
              </label>
            </div>
          </div>
        </div>

        {/* Salary Configuration Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <DollarSign className="text-green-600" size={24} />
            <h2 className="text-xl font-semibold text-gray-900">
              Salary Configuration
            </h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Monthly Salary Amount (THB)
              </label>
              <input
                type="number"
                value={salaryConfig.default_salary_amount}
                onChange={(e) => setSalaryConfig({
                  ...salaryConfig,
                  default_salary_amount: parseFloat(e.target.value) || 0
                })}
                placeholder="25000"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
              />
              <p className="mt-1 text-sm text-gray-500">
                Your default monthly salary. Auto-generated every month.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Salary Day of Month
              </label>
              <input
                type="number"
                min="1"
                max="31"
                value={salaryConfig.salary_day_of_month}
                onChange={(e) => setSalaryConfig({
                  ...salaryConfig,
                  salary_day_of_month: parseInt(e.target.value) || 1
                })}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
              />
              <p className="mt-1 text-sm text-gray-500">
                Day of month when salary is received (1-31)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Income Category
              </label>
              <input
                type="text"
                value={salaryConfig.salary_category}
                onChange={(e) => setSalaryConfig({
                  ...salaryConfig,
                  salary_category: e.target.value
                })}
                placeholder="Salary"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
              />
              <p className="mt-1 text-sm text-gray-500">
                Category name for salary entries in analytics
              </p>
            </div>
          </div>

          <div className="flex justify-end items-center gap-3 mt-4 flex-wrap">
            {salarySaveSuccess && (
              <span className="text-green-600 text-sm font-medium">
                ✓ Salary config saved successfully!
              </span>
            )}
            {salaryUpdatedMessage && (
              <span className="text-blue-600 text-sm font-medium">
                {salaryUpdatedMessage}
              </span>
            )}
            <button
              onClick={handleSaveSalary}
              disabled={salarySaving}
              className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 transition-colors"
            >
              <Save size={18} />
              {salarySaving ? 'Saving...' : 'Save Salary Config'}
            </button>
          </div>
        </div>

        {/* OCR Corrections Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Settings className="text-purple-600" size={24} />
              <h2 className="text-xl font-semibold text-gray-900">
                OCR Corrections
              </h2>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">
                {ocrCorrections.count} corrections
              </span>
              <button
                onClick={handleReloadCorrections}
                className="p-1.5 text-purple-600 hover:bg-purple-50 rounded transition-colors"
                title="Reload corrections from file"
              >
                <RefreshCw size={16} />
              </button>
            </div>
          </div>

          {/* Add new correction */}
          <div className="mb-6 p-4 bg-gray-50 rounded-md">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Add New Correction</h3>
            <div className="flex gap-3 items-end">
              <div className="flex-1">
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Wrong Text (from OCR)
                </label>
                <input
                  type="text"
                  value={newWrongText}
                  onChange={(e) => setNewWrongText(e.target.value)}
                  placeholder="เน.ย."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500 text-sm"
                />
              </div>
              <div className="flex items-center text-gray-400 pb-2">
                →
              </div>
              <div className="flex-1">
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Correct Text
                </label>
                <input
                  type="text"
                  value={newCorrectText}
                  onChange={(e) => setNewCorrectText(e.target.value)}
                  placeholder="ม.ค."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500 text-sm"
                />
              </div>
              <button
                onClick={handleAddCorrection}
                disabled={!newWrongText.trim() || !newCorrectText.trim()}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:bg-gray-400 transition-colors"
              >
                <Plus size={16} />
                Add
              </button>
            </div>
            <p className="mt-2 text-xs text-gray-500">
              Map common OCR errors to correct text. Applied automatically before parsing.
              If you edit the JSON file directly, click the reload button to apply changes.
            </p>
          </div>

          {/* Existing corrections list */}
          {ocrCorrections.count > 0 ? (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {Object.entries(ocrCorrections.corrections).map(([wrong, correct]) => (
                <div
                  key={wrong}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center gap-3 flex-1">
                    <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-mono">
                      {wrong}
                    </span>
                    <span className="text-gray-400">→</span>
                    <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-mono">
                      {correct}
                    </span>
                  </div>
                  <button
                    onClick={() => handleDeleteCorrection(wrong)}
                    className="p-1.5 text-red-600 hover:bg-red-50 rounded transition-colors"
                    title="Delete correction"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500 text-sm">
              No OCR corrections yet. Add one above to fix common OCR errors.
            </div>
          )}
        </div>

        {/* Info Card */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <Info className="text-blue-600 mt-0.5" size={18} />
            <div className="text-sm text-blue-800">
              <strong>How it works:</strong>
              <ul className="mt-2 list-disc list-inside space-y-1">
                <li>Enter your name once in settings</li>
                <li>Upload receipts as usual</li>
                <li>System automatically classifies as:
                  <span className="ml-2 inline-flex items-center gap-1">
                    <span className="px-2 py-0.5 bg-red-100 text-red-800 rounded text-xs">↑ Sending</span>
                    <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded text-xs">↓ Receiving</span>
                  </span>
                </li>
                <li>You can correct wrong classifications in Review page</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end items-center gap-3">
          {saveSuccess && (
            <span className="text-green-600 text-sm font-medium">
              ✓ Settings saved successfully!
            </span>
          )}
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
          >
            <Save size={18} />
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
}
