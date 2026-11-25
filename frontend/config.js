// API is served from the same origin at /app/. A standalone frontend uses port 8000.
export const API_BASE_URL = location.pathname.startsWith('/app/')
  ? location.origin
  : 'http://127.0.0.1:8000';
export const REQUEST_TIMEOUT_MS = 10_000;
