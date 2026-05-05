import api, { API_URL } from './api';
import { getToken } from '../utils/auth';

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

    const url = `/export/excel?${params.toString()}`;

    // Use api client to get the file with auth headers
    const response = await api.get(url, {
      responseType: 'blob'
    });

    // Create blob URL for download
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;

    // Get filename from Content-Disposition header or use default
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'OCR_Bank_Export.xlsx';
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename=(?:"([^"]+)"|([^;\s]+))/);
      if (filenameMatch) {
        filename = filenameMatch[1] || filenameMatch[2];
      }
    }

    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  /**
   * Get export service status
   */
  async getExportStatus(): Promise<any> {
    const response = await api.get('/export/status');
    return response.data;
  }
}

export default new ExportService();
