import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Upload, FileText, MessageSquare, BarChart3, Home } from 'lucide-react';
import UploadPage from './pages/Upload';
import ReviewPage from './pages/Review';
import ReceiptsListPage from './pages/ReceiptsList';
import ChatPage from './pages/Chat';

function App() {
  return (
    <Router>
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
                <NavLink to="/chat" icon={<MessageSquare size={20} />}>
                  Chat
                </NavLink>
                <NavLink to="/analytics" icon={<BarChart3 size={20} />}>
                  Analytics
                </NavLink>
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
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
          </Routes>
        </main>
      </div>
    </Router>
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

// Placeholder pages
function Dashboard() {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Receipts</h3>
          <p className="text-3xl font-bold text-blue-600">0</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Amount</h3>
          <p className="text-3xl font-bold text-green-600">฿0.00</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Pending Review</h3>
          <p className="text-3xl font-bold text-yellow-600">0</p>
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
