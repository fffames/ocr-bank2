import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Upload, FileText, MessageSquare, BarChart3, Home, Code2, User, Grid3x3, Settings as SettingsIcon } from 'lucide-react';
import { ErrorBoundary } from './components/ErrorBoundary';
import UploadPage from './pages/Upload';
import ReviewPage from './pages/Review';
import ReceiptsListPage from './pages/ReceiptsList';
import ReceiptsListDebugPage from './pages/ReceiptsListDebug';
import ChatPage from './pages/Chat';
import SettingsPage from './pages/Settings';
import TemplateBuilder from './pages/developer/TemplateBuilder';
import TemplateManagement from './pages/developer/TemplateManagement';
import { receiptService } from './services/receiptService';
import './styles/developer.css';

function App() {
  const [mode, setMode] = useState<'user' | 'developer'>('user');

  return (
    <ErrorBoundary>
      <Router>
        {mode === 'developer' ? (
          <DeveloperModeApp onModeChange={setMode} />
        ) : (
          <UserModeApp onModeChange={setMode} />
        )}
      </Router>
    </ErrorBoundary>
  );
}

function UserModeApp({ onModeChange }: { onModeChange: (mode: 'user' | 'developer') => void }) {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="flex items-center space-x-2">
                <FileText className="h-8 w-8 text-blue-600" />
                <span className="text-xl font-bold text-gray-900">OCR Bank</span>
              </Link>
            </div>

            <div className="flex items-center space-x-4">
              <NavLink to="/" icon={<Home size={20} />}>
                Dashboard
              </NavLink>
              <NavLink to="/upload" icon={<Upload size={20} />}>
                Upload
              </NavLink>
              <NavLink to="/receipts" icon={<FileText size={20} />}>
                Receipts
              </NavLink>
              <NavLink to="/settings" icon={<SettingsIcon size={20} />}>
                Settings
              </NavLink>
              <NavLink to="/chat" icon={<MessageSquare size={20} />}>
                Chat
              </NavLink>
              <NavLink to="/analytics" icon={<BarChart3 size={20} />}>
                Analytics
              </NavLink>
              <button
                onClick={() => onModeChange('developer')}
                className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
              >
                <Code2 size={20} />
                <span>Developer Mode</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/review" element={<ReviewPage />} />
          <Route path="/receipts" element={<ReceiptsListPage />} />
          <Route path="/receipts-debug" element={<ReceiptsListDebugPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
        </Routes>
      </main>
    </div>
  );
}

function DeveloperModeApp({ onModeChange }: { onModeChange: (mode: 'user' | 'developer') => void }) {
  return (
    <div className="min-h-screen">
      {/* Developer Navigation */}
      <nav className="border-b border-[var(--dev-border)] bg-[var(--dev-bg-secondary)]/90 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-6">
              <Link to="/developer/templates" className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-br from-[var(--dev-accent)] to-[#00b4d8] rounded-lg flex items-center justify-center">
                  <Grid3x3 className="h-5 w-5 text-[var(--dev-bg-primary)]" />
                </div>
                <span className="text-xl font-bold text-[var(--dev-text-primary)]">OCR Developer</span>
              </Link>
              <DevNavLink to="/developer/templates" icon={<Grid3x3 size={18} />}>
                Templates
              </DevNavLink>
              <DevNavLink to="/developer/template-builder" icon={<Code2 size={18} />}>
                Builder
              </DevNavLink>
            </div>

            <div className="flex items-center space-x-4">
              <button
                onClick={() => onModeChange('user')}
                className="flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium bg-[var(--dev-bg-tertiary)] text-[var(--dev-text-primary)] border border-[var(--dev-border)] hover:border-[var(--dev-accent)] transition-colors"
              >
                <User size={18} />
                <span>User Mode</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <Routes>
        <Route path="/developer/templates" element={<TemplateManagement />} />
        <Route path="/developer/template-builder" element={<TemplateBuilder />} />
        <Route path="/developer/template-builder/:templateId" element={<TemplateBuilder />} />
      </Routes>
    </div>
  );
}

function NavLink({ to, children, icon }: { to: string; children: React.ReactNode; icon: React.ReactNode }) {
  return (
    <Link
      to={to}
      className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-gray-100 transition-colors"
    >
      {icon}
      <span>{children}</span>
    </Link>
  );
}

function DevNavLink({ to, children, icon }: { to: string; children: React.ReactNode; icon: React.ReactNode }) {
  const location = useLocation();
  const isActive = location.pathname === to || location.pathname.startsWith(to + '/');

  return (
    <Link
      to={to}
      className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
        isActive
          ? 'text-[var(--dev-accent)] bg-[var(--dev-accent-dim)]'
          : 'text-[var(--dev-text-secondary)] hover:text-[var(--dev-text-primary)] hover:bg-[var(--dev-bg-tertiary)]'
      }`}
    >
      {icon}
      <span>{children}</span>
    </Link>
  );
}

// Placeholder pages
function Dashboard() {
  const [stats, setStats] = useState({
    total_receipts: 0,
    total_amount: 0,
    pending_count: 0,
    reviewed_count: 0,
    confirmed_count: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const data = await receiptService.getStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Receipts</h3>
          <p className="text-3xl font-bold text-blue-600">
            {loading ? '...' : stats.total_receipts}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Amount</h3>
          <p className="text-3xl font-bold text-green-600">
            {loading ? '...' : `฿${stats.total_amount.toFixed(2)}`}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Pending Review</h3>
          <p className="text-3xl font-bold text-yellow-600">
            {loading ? '...' : stats.pending_count}
          </p>
        </div>
      </div>

      {/* Additional Stats */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Reviewed</h3>
          <p className="text-2xl font-bold text-blue-600">
            {loading ? '...' : stats.reviewed_count}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Confirmed</h3>
          <p className="text-2xl font-bold text-green-600">
            {loading ? '...' : stats.confirmed_count}
          </p>
        </div>
      </div>
    </div>
  );
}


function AnalyticsPage() {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Analytics</h1>
      <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-200">
        <p className="text-gray-600 text-center">Analytics coming soon...</p>
      </div>
    </div>
  );
}

export default App;
