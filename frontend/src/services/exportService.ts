import { API_URL } from './api';

export interface ExportFilters {
  date_from?: string;
  date_to?: string;
  transaction_type?: 'sending' | 'receiving' | 'all';
  status?: 'pending' | 'reviewed' | 'confirmed' | 'all';
}

class ExportService {
  /**
   * Export receipts to Excel file with filters
   */
  async exportToExcel(filters: ExportFilters): Promise<void> {
    const params = new URLSearchParams();

    if (filters.date_from) {
      params.append('date_from', filters.date_from);
    }
    if (filters.date_to) {
      params.append('date_to', filters.date_to);
    }
    if (filters.transaction_type) {
      params.append('transaction_type', filters.transaction_type);
    }
    if (filters.status) {
      params.append('status', filters.status);
    }

    const url = `${API_URL}/api/export/excel?${params.toString()}`;

    // Trigger browser download
    window.location.href = url;
  }

  /**
   * Get export service status
   */
  async getExportStatus(): Promise<any> {
    const response = await fetch(`${API_URL}/api/export/status`);
    if (!response.ok) {
      throw new Error('Failed to get export status');
    }
    return response.json();
  }
}

export default new ExportService();
