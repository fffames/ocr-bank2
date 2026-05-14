import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, useNavigate, Navigate } from 'react-router-dom';
import { Upload, FileText, MessageSquare, BarChart3, Home, Code2, User, Grid3x3, Settings as SettingsIcon, LogOut, Shield, Menu, X } from 'lucide-react';
import { ErrorBoundary } from './components/ErrorBoundary';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import UploadPage from './pages/Upload';
import ReviewPage from './pages/Review';
import ReceiptsListPage from './pages/ReceiptsList';
import ReceiptsListDebugPage from './pages/ReceiptsListDebug';
import ChatPage from './pages/Chat';
import SettingsPage from './pages/Settings';
import AnalyticsPage from './pages/Analytics';
import Admin from './pages/Admin';
import TemplateBuilder from './pages/developer/TemplateBuilder';
import TemplateManagement from './pages/developer/TemplateManagement';
import { receiptService } from './services/receiptService';
import { getUser, logoutUser } from './utils/auth';
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
  const navigate = useNavigate();
  const currentUser = getUser();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logoutUser();
    navigate('/login');
  };

  const navLinks = [
    { to: '/dashboard', icon: <Home size={20} />, label: 'Dashboard' },
    { to: '/upload', icon: <Upload size={20} />, label: 'Upload' },
    { to: '/receipts', icon: <FileText size={20} />, label: 'Receipts' },
    { to: '/settings', icon: <SettingsIcon size={20} />, label: 'Settings' },
    { to: '/chat', icon: <MessageSquare size={20} />, label: 'Chat' },
    { to: '/analytics', icon: <BarChart3 size={20} />, label: 'Analytics' },
    ...(currentUser?.is_admin ? [{ to: '/admin', icon: <Shield size={20} />, label: 'Admin' }] : []),
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="flex items-center space-x-2">
                <FileText className="h-8 w-8 text-blue-600" />
                <span className="text-xl font-bold text-gray-900">OCR Bank</span>
              </Link>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-4">
              {navLinks.map((link) => (
                <NavLink key={link.to} to={link.to} icon={link.icon}>
                  {link.label}
                </NavLink>
              ))}
              <button
                onClick={() => onModeChange('developer')}
                className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
              >
                <Code2 size={20} />
                <span className="hidden lg:inline">Developer Mode</span>
              </button>
              <div className="flex items-center space-x-2 border-l border-gray-300 pl-4">
                <span className="text-sm text-gray-600 hidden sm:inline">
                  {currentUser?.name || currentUser?.email?.split('@')[0]}
                </span>
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-1 px-2 py-1 rounded text-sm text-gray-600 hover:bg-gray-100 transition-colors"
                  title="Logout"
                >
                  <LogOut size={16} />
                </button>
              </div>
            </div>

            {/* Mobile menu button */}
            <div className="flex items-center md:hidden">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 rounded-md text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
              >
                {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-gray-200 bg-white">
            <div className="px-2 pt-2 pb-3 space-y-1">
              {navLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center space-x-3 px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-blue-600 hover:bg-gray-100"
                >
                  {link.icon}
                  <span>{link.label}</span>
                </Link>
              ))}
              <button
                onClick={() => {
                  onModeChange('developer');
                  setMobileMenuOpen(false);
                }}
                className="flex items-center space-x-3 w-full px-3 py-2 rounded-md text-base font-medium bg-gray-100 text-gray-700 hover:bg-gray-200"
              >
                <Code2 size={20} />
                <span>Developer Mode</span>
              </button>
              <div className="border-t border-gray-200 pt-2 mt-2">
                <div className="px-3 py-2 text-sm text-gray-600">
                  {currentUser?.name || currentUser?.email?.split('@')[0]}
                </div>
                <button
                  onClick={() => {
                    handleLogout();
                    setMobileMenuOpen(false);
                  }}
                  className="flex items-center space-x-3 w-full px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-100"
                >
                  <LogOut size={20} />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* Main Content */}
      <main className="w-full px-3 sm:px-6 lg:px-8 py-4 sm:py-8">
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Navigate to="/dashboard" />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/upload"
            element={
              <ProtectedRoute>
                <UploadPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/review"
            element={
              <ProtectedRoute>
                <ReviewPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/receipts"
            element={
              <ProtectedRoute>
                <ReceiptsListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/receipts-debug"
            element={
              <ProtectedRoute>
                <ReceiptsListDebugPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <SettingsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/chat"
            element={
              <ProtectedRoute>
                <ChatPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/analytics"
            element={
              <ProtectedRoute>
                <AnalyticsPage />
              </ProtectedRoute>
            }
          />

          {/* Admin route - protected and admin-only */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute>
                <Admin />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
    </div>
  );
}

function DeveloperModeApp({ onModeChange }: { onModeChange: (mode: 'user' | 'developer') => void }) {
  const navigate = useNavigate();
  const currentUser = getUser();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logoutUser();
    navigate('/login');
  };

  return (
    <div className="min-h-screen">
      {/* Developer Navigation */}
      <nav className="border-b border-[var(--dev-border)] bg-[var(--dev-bg-secondary)]/90 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-6">
              <Link to="/developer/templates" className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-br from-[var(--dev-accent)] to-[#00b4d8] rounded-lg flex items-center justify-center">
                  <Grid3x3 className="h-5 w-5 text-[var(--dev-bg-primary)]" />
                </div>
                <span className="text-xl font-bold text-[var(--dev-text-primary)]">OCR Developer</span>
              </Link>
              <div className="hidden md:flex items-center space-x-6">
                <DevNavLink to="/developer/templates" icon={<Grid3x3 size={18} />}>
                  Templates
                </DevNavLink>
                <DevNavLink to="/developer/template-builder" icon={<Code2 size={18} />}>
                  Builder
                </DevNavLink>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <span className="text-sm text-[var(--dev-text-secondary)] hidden sm:inline">
                {currentUser?.name || currentUser?.email?.split('@')[0]}
              </span>
              <button
                onClick={handleLogout}
                className="hidden sm:flex items-center space-x-1 px-2 py-1 rounded text-sm text-[var(--dev-text-secondary)] hover:bg-[var(--dev-bg-tertiary)] transition-colors"
                title="Logout"
              >
                <LogOut size={16} />
              </button>
              <button
                onClick={() => onModeChange('user')}
                className="hidden md:flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium bg-[var(--dev-bg-tertiary)] text-[var(--dev-text-primary)] border border-[var(--dev-border)] hover:border-[var(--dev-accent)] transition-colors"
              >
                <User size={18} />
                <span>User Mode</span>
              </button>
              {/* Mobile menu button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 rounded-md text-[var(--dev-text-secondary)] hover:bg-[var(--dev-bg-tertiary)] focus:outline-none"
              >
                {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-[var(--dev-border)] bg-[var(--dev-bg-secondary)]">
            <div className="px-2 pt-2 pb-3 space-y-1">
              <Link
                to="/developer/templates"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center space-x-3 px-3 py-2 rounded-md text-base font-medium text-[var(--dev-text-secondary)] hover:text-[var(--dev-text-primary)] hover:bg-[var(--dev-bg-tertiary)]"
              >
                <Grid3x3 size={20} />
                <span>Templates</span>
              </Link>
              <Link
                to="/developer/template-builder"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center space-x-3 px-3 py-2 rounded-md text-base font-medium text-[var(--dev-text-secondary)] hover:text-[var(--dev-text-primary)] hover:bg-[var(--dev-bg-tertiary)]"
              >
                <Code2 size={20} />
                <span>Builder</span>
              </Link>
              <div className="border-t border-[var(--dev-border)] pt-2 mt-2">
                <div className="px-3 py-2 text-sm text-[var(--dev-text-secondary)]">
                  {currentUser?.name || currentUser?.email?.split('@')[0]}
                </div>
                <button
                  onClick={() => {
                    handleLogout();
                    setMobileMenuOpen(false);
                  }}
                  className="flex items-center space-x-3 w-full px-3 py-2 rounded-md text-base font-medium text-[var(--dev-text-secondary)] hover:bg-[var(--dev-bg-tertiary)]"
                >
                  <LogOut size={20} />
                  <span>Logout</span>
                </button>
                <button
                  onClick={() => {
                    onModeChange('user');
                    setMobileMenuOpen(false);
                  }}
                  className="flex items-center space-x-3 w-full px-3 py-2 mt-1 rounded-md text-base font-medium bg-[var(--dev-bg-tertiary)] text-[var(--dev-text-primary)] border border-[var(--dev-border)]"
                >
                  <User size={20} />
                  <span>User Mode</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* Main Content */}
      <Routes>
        <Route
          path="/developer/templates"
          element={
            <ProtectedRoute>
              <TemplateManagement />
            </ProtectedRoute>
          }
        />
        <Route
          path="/developer/template-builder"
          element={
            <ProtectedRoute>
              <TemplateBuilder />
            </ProtectedRoute>
          }
        />
        <Route
          path="/developer/template-builder/:templateId"
          element={
            <ProtectedRoute>
              <TemplateBuilder />
            </ProtectedRoute>
          }
        />
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
    sending_amount: 0,
    receiving_amount: 0,
    pending_count: 0,
    reviewed_count: 0,
    confirmed_count: 0,
    sending_count: 0,
    receiving_count: 0
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
      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4 sm:mb-6">Dashboard</h1>

      {/* Main Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        <div className="bg-white p-4 sm:p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-base sm:text-lg font-semibold text-gray-700 mb-2">Total Receipts</h3>
          <p className="text-2xl sm:text-3xl font-bold text-blue-600">
            {loading ? '...' : stats.total_receipts}
          </p>
        </div>

        {/* Net Amount (can be positive or negative) */}
        <div className="bg-white p-4 sm:p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-base sm:text-lg font-semibold text-gray-700 mb-2">Net Balance</h3>
          <p className={`text-2xl sm:text-3xl font-bold ${stats.total_amount >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {loading ? '...' : `${stats.total_amount >= 0 ? '+' : ''}฿${stats.total_amount.toFixed(2)}`}
          </p>
        </div>

        <div className="bg-white p-4 sm:p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-base sm:text-lg font-semibold text-gray-700 mb-2">Pending Review</h3>
          <p className="text-2xl sm:text-3xl font-bold text-yellow-600">
            {loading ? '...' : stats.pending_count}
          </p>
        </div>
      </div>

      {/* Income vs Expenses */}
      <div className="mt-4 sm:mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
        <div className="bg-white p-4 sm:p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-base sm:text-lg font-semibold text-gray-700 mb-2">Total Received (Income)</h3>
          <p className="text-xl sm:text-2xl font-bold text-green-600">
            {loading ? '...' : `+฿${stats.receiving_amount.toFixed(2)}`}
          </p>
          <p className="text-sm text-gray-500 mt-1">
            {stats.receiving_count} transactions
          </p>
        </div>

        <div className="bg-white p-4 sm:p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-base sm:text-lg font-semibold text-gray-700 mb-2">Total Sent (Expenses)</h3>
          <p className="text-xl sm:text-2xl font-bold text-red-600">
            {loading ? '...' : `-฿${stats.sending_amount.toFixed(2)}`}
          </p>
          <p className="text-sm text-gray-500 mt-1">
            {stats.sending_count} transactions
          </p>
        </div>
      </div>

      {/* Status Counts */}
      <div className="mt-4 sm:mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
        <div className="bg-white p-4 sm:p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-base sm:text-lg font-semibold text-gray-700 mb-2">Reviewed</h3>
          <p className="text-xl sm:text-2xl font-bold text-blue-600">
            {loading ? '...' : stats.reviewed_count}
          </p>
        </div>
        <div className="bg-white p-4 sm:p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-base sm:text-lg font-semibold text-gray-700 mb-2">Confirmed</h3>
          <p className="text-xl sm:text-2xl font-bold text-green-600">
            {loading ? '...' : stats.confirmed_count}
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
