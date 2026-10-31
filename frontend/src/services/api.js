import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
const DIRECT_BACKEND_URL = 'http://127.0.0.1:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('nagarnexus_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error?.config;
    const isEmptyProxyError =
      !error?.response ||
      (error.response.status >= 500 && !error.response.data?.detail);

    if (config && !config._retriedDirect && isEmptyProxyError && config.baseURL !== DIRECT_BACKEND_URL) {
      config._retriedDirect = true;
      config.baseURL = DIRECT_BACKEND_URL;
      return api.request(config);
    }
    return Promise.reject(error);
  }
);

export const extractErrorMessage = (error) => {
  if (error?.response?.data?.detail) {
    const detail = error.response.data.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map((d) => d.msg?.replace(/^Value error,\s*/i, '') || JSON.stringify(d)).join(', ');
    }
  }
  if (error?.response?.status === 500 && !error?.response?.data?.detail) {
    return 'Backend API server (http://127.0.0.1:8000) was unreachable or returned an empty 500 error.';
  }
  return error?.message || 'An unexpected error occurred while communicating with the server.';
};

export default api;
