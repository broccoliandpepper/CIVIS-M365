import { state } from "./state.js";

const API = "/api/v1";

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }

  const response = await fetch(`${API}${path}`, {
    ...options,
    headers,
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message = payload?.detail || payload?.message || response.statusText;
    throw new Error(message);
  }

  return payload;
}

export function apiHealth() {
  return fetch("/health").then((r) => r.json());
}

export function apiLogin(username, password) {
  const body = new URLSearchParams({ username, password });
  return request("/auth/login", { method: "POST", body });
}

export function apiMe() {
  return request("/auth/me");
}

export function apiKpis(days = 30) {
  return request(`/dashboard/kpis?days=${days}`);
}

export function apiSignins(page = 1, pageSize = 25) {
  return request(`/query/signins?page=${page}&page_size=${pageSize}`);
}

export function apiUnknownUsers(limit = 20) {
  return request(`/alerts/unknown-users?limit=${limit}`);
}

export function apiRiskyUsers(page = 1, pageSize = 25) {
  return request(`/query/risky-users?page=${page}&page_size=${pageSize}`);
}

export function apiIncidents(page = 1, pageSize = 25) {
  return request(`/query/incidents?page=${page}&page_size=${pageSize}`);
}

export function apiAuditLogs(page = 1, pageSize = 25) {
  return request(`/query/audit-logs?page=${page}&page_size=${pageSize}`);
}

export function apiSocSummary(period = "last_7_days") {
  return request(`/soc/summary?period=${encodeURIComponent(period)}`);
}

export function apiSocAnomalies(period = "last_7_days", page = 1, pageSize = 50) {
  return request(
    `/soc/anomalies?period=${encodeURIComponent(period)}&status=&page=${page}&page_size=${pageSize}`
  );
}

export function apiSocAnalyze(period = "last_7_days") {
  return request("/soc/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ period }),
  });
}

export function apiUsers() {
  return request("/auth/users");
}

export function apiClearData(sourceType) {
  return request("/admin/clear-data", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source_type: sourceType }),
  });
}

export function apiResetPassword(userId, newPassword) {
  return request("/auth/reset-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, new_password: newPassword }),
  });
}

export function apiToggleUser(userId, isActive) {
  return request("/auth/toggle-user", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, is_active: isActive }),
  });
}

export async function apiUpload(endpoint, file) {
  const formData = new FormData();
  formData.append("file", file);
  return request(endpoint, { method: "POST", body: formData });
}
