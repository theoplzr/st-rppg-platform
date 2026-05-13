const rawBase = import.meta.env.VITE_API_URL || "/api";

export const API_BASE = rawBase.replace(/\/+$/, "");

export function apiUrl(path = "") {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${normalizedPath}`;
}
