import axios from 'axios';

// Resolve base URL robustly: supports full backend URL with or without '/api' suffix,
// and falls back to local Vite development proxy '/api' when not specified.
let rawBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
let resolvedBaseUrl = rawBaseUrl.trim();

if (resolvedBaseUrl.startsWith('http') && !resolvedBaseUrl.endsWith('/api') && !resolvedBaseUrl.endsWith('/api/')) {
  resolvedBaseUrl = `${resolvedBaseUrl.replace(/\/+$/, '')}/api`;
}

const api = axios.create({
  baseURL: resolvedBaseUrl,
});

// Request interceptor to attach JWT token and handle FormData Content-Type
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('brandguard_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // When sending FormData, remove Content-Type so Axios and the browser
    // automatically generate the multipart/form-data boundary delimiter.
    if (
      config.data instanceof FormData ||
      (config.data && Object.prototype.toString.call(config.data) === '[object FormData]')
    ) {
      delete config.headers['Content-Type'];
      delete config.headers['content-type'];
      if (typeof config.headers.setContentType === 'function') {
        config.headers.setContentType(false);
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle unauthenticated 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Auto logout on token expiration or invalid token
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        localStorage.removeItem('brandguard_token');
        localStorage.removeItem('brandguard_user');
        window.location.href = '/login?expired=true';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
