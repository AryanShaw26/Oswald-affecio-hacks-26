import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor — attach auth token when available (V2+)
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('trustmatch_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor — centralised error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[TrustMatch API]', error.response?.status, error.message);
    return Promise.reject(error);
  }
);

export default api;

