import api from './api';

export const userService = {
  getSettings: async () => {
    const response = await api.get('/user/settings');
    return response.data;
  },

  updateSettings: async (settings: {
    user_name?: string;
    name_variations?: string[];
    auto_classify?: boolean;
  }) => {
    const response = await api.put('/user/settings', settings);
    return response.data;
  }
};
