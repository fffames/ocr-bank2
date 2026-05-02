import { useState, useEffect } from 'react';
import { Receipt } from '../types/receipt';
import { receiptService } from '../services/receiptService';

export default function ReceiptsListDebugPage() {
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const testAPI = async () => {
      console.log("=== Starting API Test ===");
      try {
        console.log("1. Calling receiptService.getReceipts()...");
        const data = await receiptService.getReceipts({ limit: 5 });
        console.log("2. API Response:", data);
        console.log("3. Data type:", typeof data);
        console.log("4. Is array?", Array.isArray(data));
        console.log("5. First item:", data[0]);

        setReceipts(data);
        setError(null);
      } catch (err) {
        console.error("API Error:", err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    testAPI();
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Receipts Debug Page</h1>

      {loading && <p className="text-blue-600">Loading...</p>}

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Debug Information</h2>
        <ul className="space-y-2 text-sm">
          <li><strong>Loading:</strong> {loading.toString()}</li>
          <li><strong>Error:</strong> {error || 'None'}</li>
          <li><strong>Receipts Count:</strong> {receipts.length}</li>
          <li><strong>Receipts Type:</strong> {Array.isArray(receipts) ? 'Array' : typeof receipts}</li>
        </ul>

        {receipts.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-semibold mb-2">First Receipt (Raw Data)</h3>
            <pre className="bg-gray-100 p-4 rounded text-xs overflow-auto">
              {JSON.stringify(receipts[0], null, 2)}
            </pre>
          </div>
        )}

        <div className="mt-6">
          <h3 className="text-lg font-semibold mb-2">All Receipts (Simple Table)</h3>
          <table className="min-w-full border border-gray-300">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 border">ID</th>
                <th className="px-4 py-2 border">Filename</th>
                <th className="px-4 py-2 border">Date</th>
                <th className="px-4 py-2 border">Amount</th>
              </tr>
            </thead>
            <tbody>
              {receipts.map((receipt) => (
                <tr key={receipt.id}>
                  <td className="px-4 py-2 border">{receipt.id}</td>
                  <td className="px-4 py-2 border">{receipt.filename}</td>
                  <td className="px-4 py-2 border">{receipt.extracted_date || 'N/A'}</td>
                  <td className="px-4 py-2 border">{receipt.amount || 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
