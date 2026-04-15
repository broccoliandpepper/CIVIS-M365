import { resetSessionState, state } from "./state.js";

const API = "/api/v1";

function toQuery(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    query.set(key, String(value));
  });
  return query.toString();
}

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

  if (response.status === 401) {
    resetSessionState();
    window.dispatchEvent(new CustomEvent("siem:unauthorized"));
  }

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

export function apiLogout() {
  return request("/auth/logout", { method: "POST" });
}

export function apiKpis(days = 30) {
  return request(`/dashboard/kpis?days=${days}`);
}

export function apiSignins(page = 1, pageSize = 25, filters = {}) {
  const query = toQuery({ page, page_size: pageSize, ...filters });
  return request(`/query/signins?${query}`);
}

export function apiUnknownUsers(limit = 20) {
  return request(`/alerts/unknown-users?limit=${limit}`);
}

export function apiApproveUnknownUser(userPrincipal, notes = "") {
  return request(`/alerts/unknown-users/${encodeURIComponent(userPrincipal)}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ notes }),
  });
}

export function apiRejectUnknownUser(userPrincipal, notes = "") {
  return request(`/alerts/unknown-users/${encodeURIComponent(userPrincipal)}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ notes }),
  });
}

export function apiRiskyUsers(page = 1, pageSize = 25, filters = {}) {
  const query = toQuery({ page, page_size: pageSize, ...filters });
  return request(`/query/risky-users?${query}`);
}

export function apiIncidents(page = 1, pageSize = 25, filters = {}) {
  const query = toQuery({ page, page_size: pageSize, ...filters });
  return request(`/query/incidents?${query}`);
}

export function apiAuditLogs(page = 1, pageSize = 25, filters = {}) {
  const query = toQuery({ page, page_size: pageSize, ...filters });
  return request(`/query/audit-logs?${query}`);
}

export function apiTruthList(page = 1, pageSize = 25, filters = {}) {
  const query = toQuery({ page, page_size: pageSize, ...filters });
  return request(`/query/truth-list?${query}`);
}

export function apiSocSummary(filters = {}) {
  const query = toQuery({
    period: filters.period || "last_7_days",
    start_date: filters.start_date,
    end_date: filters.end_date,
  });
  return request(`/soc/summary?${query}`);
}

export function apiSocAnomalies(filters = {}, page = 1, pageSize = 50) {
  const query = toQuery({
    period: filters.period || "last_7_days",
    start_date: filters.start_date,
    end_date: filters.end_date,
    event_type: filters.event_type,
    severity: filters.severity,
    status: filters.status,
    page,
    page_size: pageSize,
  });
  return request(`/soc/anomalies?${query}`);
}

export function apiSocAnalyze(filters = {}) {
  return request("/soc/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      period: filters.period || "last_7_days",
      start_date: filters.start_date || null,
      end_date: filters.end_date || null,
    }),
  });
}

export function apiSocExportHtml(filters = {}) {
  return request("/soc/export/html", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      period: filters.period || "last_7_days",
      start_date: filters.start_date || null,
      end_date: filters.end_date || null,
      include_details: true,
      anomalies_only: false,
    }),
  });
}

export function apiUsers() {
  return request("/auth/users");
}

export function apiRegister(username, password, email = "", role = "viewer") {
  return request("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, email: email || null, role }),
  });
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

export function apiUpdateUserRole(userId, role) {
  return request("/auth/update-role", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, role }),
  });
}

export function apiLifecycleStatus() {
  return request("/lifecycle/status");
}

export function apiLifecycleBackups(limit = 20) {
  return request(`/lifecycle/backups?limit=${limit}`);
}

export function apiLifecycleLogs(limit = 20) {
  return request(`/lifecycle/logs?limit=${limit}`);
}

export function apiCreateBackup() {
  return request("/lifecycle/backup/create", { method: "POST" });
}

export function apiVerifyBackup(backupId) {
  return request(`/lifecycle/backup/${encodeURIComponent(backupId)}/verify`, { method: "POST" });
}

export function apiInspectBackup(backupId) {
  return request(`/lifecycle/backup/${encodeURIComponent(backupId)}/contents`);
}

export function apiRestoreBackup(backupId) {
  return request(`/lifecycle/backup/${encodeURIComponent(backupId)}/restore`, { method: "POST" });
}

export async function apiUpload(endpoint, file) {
  const formData = new FormData();
  formData.append("file", file);
  return request(endpoint, { method: "POST", body: formData });
}
