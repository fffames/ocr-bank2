import api, { directApi } from './api';
import { ReceiptUpdate } from '../types/receipt';

export const receiptService = {
  // Upload images and process with OCR
  uploadImages: async (files: File[]) => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    // Use direct API to bypass proxy for multipart data
    const response = await directApi.post('/upload/', formData);
    return response.data;
  },

  // Get all receipts
  getReceipts: async (params?: {
    skip?: number;
    limit?: number;
    status?: string;
    date_from?: string;
    date_to?: string;
    sender?: string;
  }) => {
    const response = await api.get('/receipts/', { params });
    return response.data;
  },

  // Get single receipt
  getReceipt: async (id: number) => {
    const response = await api.get(`/receipts/${id}`);
    return response.data;
  },

  // Update receipt
  updateReceipt: async (id: number, data: ReceiptUpdate) => {
    const response = await api.put(`/receipts/${id}`, data);
    return response.data;
  },

  // Confirm receipt
  confirmReceipt: async (id: number) => {
    const response = await api.post(`/receipts/${id}/confirm`);
    return response.data;
  },

  // Delete receipt
  deleteReceipt: async (id: number) => {
    const response = await api.delete(`/receipts/${id}`);
    return response.data;
  },

  // Get statistics
  getStats: async () => {
    const response = await api.get('/receipts/stats/overview');
    return response.data;
  },
};
