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

// ─── Auth methods ─────────────────────────────────────────────── (V2)
export const login = async (email, password) => {
  const res = await api.post('/auth/login', { email, password });
  return res.data; // { access_token, token_type }
};

export const register = async (name, email, password) => {
  const res = await api.post('/auth/register', { name, email, password });
  return res.data; // { access_token, token_type }
};

export const logout = () => {
  localStorage.removeItem('trustmatch_token');
  localStorage.removeItem('trustmatch_user');
};

export const getCurrentUser = async () => {
  const res = await api.get('/auth/users/me');
  return res.data; // { id, name, email, created_at }
};

// ─── V4 — Conversation Safety ──────────────────────────────────
export const analyzeSafety = async (message) => {
  const res = await api.post('/safety/analyze', { message });
  return res.data; // { risk_level, categories, flagged, summary, recommendation }
};

// ─── V5 — Privacy Guardian ─────────────────────────────────────
export const checkPrivacy = async (message) => {
  const res = await api.post('/privacy/check', { message });
  return res.data; // { flagged, risk_level, detected_types, warning, recommendation }
};

export const getPrivacyAlerts = async () => {
  const res = await api.get('/privacy/alerts');
  return res.data; // array of PrivacyAlertRead
};

export default api;

