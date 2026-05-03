import { useState, useEffect } from 'react';
import { Settings, Save, User, Info, DollarSign } from 'lucide-react';
import { userService } from '../services/userService';
import { analyticsService, SalaryConfig } from '../services/analyticsService';

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
