function esc(value) {
  return String(value ?? "").replace(/[&<>"]/g, (s) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
  }[s]));
}

function tableOrEmpty(headers, rows, emptyText) {
  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>${headers.map((h) => `<th>${esc(h)}</th>`).join("")}</tr>
        </thead>
        <tbody>
          ${rows || `<tr><td colspan="${headers.length}">${esc(emptyText)}</td></tr>`}
        </tbody>
      </table>
    </div>
  `;
}

function pager(currentPage = 1, totalPages = 1, view = "") {
  if (!totalPages || totalPages <= 1) {
    return "";
  }

  const prevDisabled = currentPage <= 1 ? "disabled" : "";
  const nextDisabled = currentPage >= totalPages ? "disabled" : "";

  return `
    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
      <button class="btn secondary" data-page-view="${esc(view)}" data-page-action="prev" ${prevDisabled}>Precedent</button>
      <span>Page ${esc(currentPage)} / ${esc(totalPages)}</span>
      <button class="btn secondary" data-page-view="${esc(view)}" data-page-action="next" ${nextDisabled}>Suivant</button>
    </div>
  `;
}

export function renderLogin(error = "") {
  return `
    <div class="login-shell">
      <div class="login-card">
        <h2>SIEM M365 V2</h2>
        <p class="subtitle">Authentification SOC</p>
        ${error ? `<div class="notice error">${esc(error)}</div>` : ""}
        <form id="login-form">
          <label>Utilisateur</label>
          <input class="input" name="username" value="admin" required>
          <label>Mot de passe</label>
          <input class="input" type="password" name="password" required>
          <button class="btn" type="submit">Se connecter</button>
        </form>
      </div>
    </div>
  `;
}

export function renderAppShell(user) {
  const username = esc(user?.username || "");
  const role = esc(user?.role || "");
  const adminNav = user?.role === "admin"
    ? `<button class="nav-btn" data-view="admin">Admin</button>`
    : "";
  return `
    <div class="app-shell">
      <header class="topbar">
        <h1>SIEM M365 V2</h1>
        <div class="meta">
          <span>${username} (${role})</span>
          <button class="btn secondary" id="logout-btn">Logout</button>
        </div>
      </header>
      <nav class="navbar" id="navbar">
        <button class="nav-btn active" data-view="dashboard">Dashboard</button>
        <button class="nav-btn" data-view="ingestion">Ingestion</button>
        <button class="nav-btn" data-view="signins">SignIns</button>
        <button class="nav-btn" data-view="risky">Risky</button>
        <button class="nav-btn" data-view="incidents">Incidents</button>
        <button class="nav-btn" data-view="audit">Audit Logs</button>
        <button class="nav-btn" data-view="soc">SOC</button>
        <button class="nav-btn" data-view="alerts">Alertes</button>
        ${adminNav}
      </nav>
      <main class="content" id="content"></main>
    </div>
  `;
}

export function renderDashboard(kpis) {
  const items = [
    ["Connexions", kpis?.signins_total?.value ?? "-"],
    ["Echecs", kpis?.signins_failed?.value ?? "-"],
    ["Risky Users", kpis?.risky_users?.value ?? "-"],
    ["Incidents ouverts", kpis?.incidents_open?.value ?? "-"],
  ];
  return `
    <section class="grid">
      <h2>Dashboard</h2>
      <div class="grid kpi-grid">
        ${items.map(([label, value]) => `
          <article class="card">
            <div>${esc(label)}</div>
            <div class="kpi-value">${esc(value)}</div>
          </article>
        `).join("")}
      </div>
      <button class="btn" id="refresh-kpi">Rafraichir KPI</button>
    </section>
  `;
}

export function renderIngestion(resultMsg = "") {
  return `
    <section class="grid">
      <h2>Ingestion</h2>
      ${resultMsg ? `<div class="notice success">${esc(resultMsg)}</div>` : ""}
      <article class="card">
        <h3>Upload SignIns</h3>
        <input class="input" id="file-signins" type="file" accept=".json,.csv">
        <button class="btn" data-upload="/ingest/upload/signins" data-file-id="file-signins">Envoyer</button>
      </article>
      <article class="card">
        <h3>Upload Truth List</h3>
        <input class="input" id="file-truth" type="file" accept=".json,.csv">
        <button class="btn" data-upload="/ingest/upload/truth-list" data-file-id="file-truth">Envoyer</button>
      </article>
      <article class="card">
        <h3>Upload Risky Users</h3>
        <input class="input" id="file-risky" type="file" accept=".json,.csv">
        <button class="btn" data-upload="/ingest/upload/risky-users" data-file-id="file-risky">Envoyer</button>
      </article>
      <article class="card">
        <h3>Upload Incidents</h3>
        <input class="input" id="file-incidents" type="file" accept=".json,.csv">
        <button class="btn" data-upload="/ingest/upload/incidents" data-file-id="file-incidents">Envoyer</button>
      </article>
      <article class="card">
        <h3>Upload Audit Logs</h3>
        <input class="input" id="file-audit" type="file" accept=".json,.csv">
        <button class="btn" data-upload="/ingest/upload/audit-logs" data-file-id="file-audit">Envoyer</button>
      </article>
    </section>
  `;
}

export function renderSignins(data) {
  const rows = (data?.items || []).map((row) => `
    <tr>
      <td>${esc(row.timestamp)}</td>
      <td>${esc(row.user_principal)}</td>
      <td>${esc(row.display_name)}</td>
      <td>${esc(row.ip_address)}</td>
      <td>${esc(row.status)}</td>
      <td>${esc(row.app_name)}</td>
    </tr>
  `).join("");

  return `
    <section class="grid">
      <h2>SignIns</h2>
      ${tableOrEmpty(["Date", "User", "Display Name", "IP", "Status", "App"], rows, "Aucune donnee")}
      ${pager(data?.page, data?.total_pages, "signins")}
    </section>
  `;
}

export function renderAlerts(items) {
  const rows = (items || []).map((a) => `
    <tr>
      <td>${esc(a.user_principal || a.user || "")}</td>
      <td>${esc(a.first_seen || a.timestamp || "")}</td>
      <td>${esc(a.status || "pending")}</td>
    </tr>
  `).join("");

  return `
    <section class="grid">
      <h2>Alertes Nouveaux Utilisateurs</h2>
      ${tableOrEmpty(["Utilisateur", "First Seen", "Status"], rows, "Aucune alerte")}
    </section>
  `;
}

export function renderRiskyUsers(data) {
  const rows = (data?.items || []).map((row) => `
    <tr>
      <td>${esc(row.timestamp)}</td>
      <td>${esc(row.user_principal)}</td>
      <td>${esc(row.risk_level)}</td>
      <td>${esc(row.risk_state)}</td>
      <td>${esc(row.detection_type)}</td>
    </tr>
  `).join("");

  return `
    <section class="grid">
      <h2>Risky Users</h2>
      ${tableOrEmpty(["Date", "User", "Risk Level", "Risk State", "Detection"], rows, "Aucune donnee")}
      ${pager(data?.page, data?.total_pages, "risky")}
    </section>
  `;
}

export function renderIncidents(data) {
  const rows = (data?.items || []).map((row) => `
    <tr>
      <td>${esc(row.timestamp)}</td>
      <td>${esc(row.incident_id)}</td>
      <td>${esc(row.title)}</td>
      <td>${esc(row.severity)}</td>
      <td>${esc(row.status)}</td>
    </tr>
  `).join("");

  return `
    <section class="grid">
      <h2>Incidents</h2>
      ${tableOrEmpty(["Date", "Incident", "Titre", "Severite", "Status"], rows, "Aucune donnee")}
      ${pager(data?.page, data?.total_pages, "incidents")}
    </section>
  `;
}

export function renderAuditLogs(data) {
  const rows = (data?.items || []).map((row) => `
    <tr>
      <td>${esc(row.timestamp)}</td>
      <td>${esc(row.user_principal)}</td>
      <td>${esc(row.operation)}</td>
      <td>${esc(row.workload)}</td>
      <td>${esc(row.result || row.result_status)}</td>
    </tr>
  `).join("");

  return `
    <section class="grid">
      <h2>Audit Logs</h2>
      ${tableOrEmpty(["Date", "User", "Operation", "Workload", "Resultat"], rows, "Aucune donnee")}
      ${pager(data?.page, data?.total_pages, "audit")}
    </section>
  `;
}

export function renderSoc(summary, anomalies, message = "") {
  const cards = [
    ["Anomalies", summary?.total_anomalies],
    ["Critiques", summary?.critical_count],
    ["Echecs", summary?.failed_signins],
    ["Out-of-list", summary?.out_of_list_signins],
  ];
  const rows = (anomalies?.items || anomalies || []).map((row) => `
    <tr>
      <td>${esc(row.timestamp)}</td>
      <td>${esc(row.user_principal)}</td>
      <td>${esc(row.event_type)}</td>
      <td>${esc(row.severity)}</td>
      <td>${esc(row.ip_address)}</td>
      <td>${esc(row.reason)}</td>
    </tr>
  `).join("");

  return `
    <section class="grid">
      <h2>SOC</h2>
      <div>
        <button class="btn" id="soc-run-analysis">Lancer analyse</button>
      </div>
      ${message ? `<div class="notice success">${esc(message)}</div>` : ""}
      <div class="grid kpi-grid">
        ${cards.map(([label, value]) => `
          <article class="card">
            <div>${esc(label)}</div>
            <div class="kpi-value">${esc(value ?? "-")}</div>
          </article>
        `).join("")}
      </div>
      ${tableOrEmpty(["Date", "User", "Type", "Severite", "IP", "Reason"], rows, "Aucune anomalie")}
      ${pager(anomalies?.page, anomalies?.total_pages, "soc")}
    </section>
  `;
}

export function renderAdmin(users, message = "", currentUser = null) {
  const rows = (users || []).map((u) => `
    <tr>
      <td>${esc(u.id)}</td>
      <td>${esc(u.username)}</td>
      <td>${esc(u.role)}</td>
      <td>${esc(u.is_active ? "actif" : "inactif")}</td>
      <td>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="btn secondary" data-toggle-user="${esc(u.id)}" data-toggle-target="${esc(!u.is_active)}" ${currentUser?.id === u.id ? "disabled" : ""}>${u.is_active ? "Desactiver" : "Activer"}</button>
          <button class="btn secondary" data-reset-user="${esc(u.id)}">Reset Password</button>
        </div>
      </td>
    </tr>
  `).join("");

  return `
    <section class="grid">
      <h2>Administration</h2>
      ${message ? `<div class="notice warn">${esc(message)}</div>` : ""}
      <article class="card">
        <h3>Nettoyage rapide</h3>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;">
          <button class="btn secondary" data-clear="signins">Vider SignIns</button>
          <button class="btn secondary" data-clear="risky_users">Vider Risky</button>
          <button class="btn secondary" data-clear="incidents">Vider Incidents</button>
          <button class="btn secondary" data-clear="audit_logs">Vider Audit</button>
        </div>
      </article>
      ${tableOrEmpty(["ID", "Username", "Role", "Etat", "Actions"], rows, "Aucun utilisateur")}
    </section>
  `;
}
