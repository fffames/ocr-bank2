import api from './api';

export interface OCRCorrections {
  corrections: Record<string, string>;
  count: number;
}

export const ocrCorrectionService = {
  // Get all corrections
  getCorrections: async () => {
    const response = await api.get('/corrections');
    return response.data;
  },

  // Add a new correction
  addCorrection: async (wrongText: string, correctText: string) => {
    const response = await api.post('/corrections', {
      wrong_text: wrongText,
      correct_text: correctText
    });
    return response.data;
  },

  // Update a correction
  updateCorrection: async (wrongText: string, correctText: string) => {
    const response = await api.put(`/corrections/${encodeURIComponent(wrongText)}`, {
      correct_text: correctText
    });
    return response.data;
  },

  // Delete a correction
  deleteCorrection: async (wrongText: string) => {
    const response = await api.delete(`/corrections/${encodeURIComponent(wrongText)}`);
    return response.data;
  },

  // Clear all corrections
  clearCorrections: async () => {
    const response = await api.delete('/corrections');
    return response.data;
  },

  // Reload corrections from file
  reloadCorrections: async () => {
    const response = await api.post('/corrections/reload');
    return response.data;
  }
};
