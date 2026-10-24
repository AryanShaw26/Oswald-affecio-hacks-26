import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
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
    if (error.response) {
      // Server responded with an error status
      const { status, data } = error.response;
      const detail = data?.detail || error.message;
      // Don't log auth errors to console to avoid noise
      if (status !== 401) {
        console.error('[TrustMatch API]', status, detail);
      }
    } else if (error.request) {
      // Request was made but no response received (network failure / timeout)
      console.error('[TrustMatch API] Network error — no response received');
    } else {
      console.error('[TrustMatch API]', error.message);
    }
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

// ─── V6 — Safety Alerts ─────────────────────────────────────────
export const getAlerts = async () => {
  const res = await api.get('/alerts');
  return res.data; // AlertRead[]
};

export const getUnreadAlerts = async () => {
  const res = await api.get('/alerts/unread');
  return res.data; // AlertRead[]
};

export const getUnreadAlertCount = async () => {
  const res = await api.get('/alerts/unread-count');
  return res.data; // { unread_count }
};

export const markAllAlertsRead = async () => {
  const res = await api.post('/alerts/read');
  return res.data; // { message }
};

export const getAlert = async (alertId) => {
  const res = await api.get(`/alerts/${alertId}`);
  return res.data; // AlertRead
};

// ─── V6 — Reports ───────────────────────────────────────────────
export const createReport = async (reportedUserId, reportType, description, profileId = null) => {
  const res = await api.post('/reports', {
    reported_user_id: reportedUserId,
    report_type: reportType,
    description,
    profile_id: profileId,
  });
  return res.data; // ReportRead
};

export const getMyReports = async () => {
  const res = await api.get('/reports/mine');
  return res.data; // ReportRead[]
};

export const getReportsForUser = async (userId) => {
  const res = await api.get(`/reports/user/${userId}`);
  return res.data; // ReportRead[]
};

// ─── V6 — Blocks ────────────────────────────────────────────────
export const blockUser = async (blockedUserId, reason = null) => {
  const res = await api.post('/blocks', {
    blocked_user_id: blockedUserId,
    reason,
  });
  return res.data; // BlockResponse { id, message, created_at }
};

export const getBlockedUsers = async () => {
  const res = await api.get('/blocks');
  return res.data; // BlockRead[]
};

export const getBlockedIds = async () => {
  const res = await api.get('/blocks/ids');
  return res.data; // int[]
};

export const unblockUser = async (targetId) => {
  const res = await api.delete(`/blocks/${targetId}`);
  return res.data; // { message }
};

export const checkBlock = async (targetId) => {
  const res = await api.get(`/blocks/check/${targetId}`);
  return res.data; // { target_id, is_blocked }
};

// ─── V6 — Dashboard ─────────────────────────────────────────────
export const getDashboard = async () => {
  const res = await api.get('/dashboard');
  return res.data; // DashboardResponse
};

// ─── V3 — Trust Score ───────────────────────────────────────────
export const getMyTrustScore = async () => {
  const res = await api.get('/trust/me');
  return res.data; // TrustScoreRead
};

export const getProfileTrustScore = async (profileId) => {
  const res = await api.get(`/trust/profile/${profileId}`);
  return res.data; // TrustScoreRead
};

export const analyzeProfileTrust = async (profileId) => {
  const res = await api.post(`/trust/analyze/${profileId}`);
  return res.data; // TrustScoreResponse { score, risk_level, explanation, factors }
};

// ─── V2 — Profiles ──────────────────────────────────────────────
export const getMyProfile = async () => {
  const res = await api.get('/profiles/me');
  return res.data; // ProfileRead
};

export const getProfile = async (profileId) => {
  const res = await api.get(`/profiles/${profileId}`);
  return res.data; // ProfileRead
};

export default api;

