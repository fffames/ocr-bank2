import api from './api';

export const exportService = {
  exportToSheets: async (receiptIds?: number[]) => {
    const response = await api.post('/export/sheets', {
      receipt_ids: receiptIds,
      export_type: 'receipts'
    });
    return response.data;
  },

  exportSummary: async () => {
    const response = await api.post('/export/sheets', {
      receipt_ids: null,
      export_type: 'summary'
    });
    return response.data;
  },

  getExportStatus: async () => {
    const response = await api.get('/export/status');
    return response.data;
  }
};
