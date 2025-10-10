export const API_BASE = (import.meta as any).env?.VITE_API_BASE || 'http://localhost:5005';

export const apiUrl = (path: string) => `${API_BASE}${path.startsWith('/') ? '' : '/'}${path}`;
