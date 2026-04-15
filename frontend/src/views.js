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
        <h2>SPLONK SIEM M365 V2</h2>
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
    ? `<button class="nav-btn" data-view="lifecycle">Lifecycle</button><button class="nav-btn" data-view="admin">Admin</button>`
    : "";
  return `
    <div class="app-shell">
      <header class="topbar">
        <h1>SPLONK SIEM M365 V2</h1>
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
        <button class="nav-btn" data-view="truth">Truth List</button>
        <button class="nav-btn" data-view="soc">SOC</button>
        <button class="nav-btn" data-view="alerts">Alertes</button>
        ${adminNav}
      </nav>
      <main class="content" id="content"></main>
    </div>
  `;
}

export function renderLifecycle(data, currentUser = null, message = "") {
  const status = data?.status || {};
  const backups = data?.backups || [];
  const logs = data?.logs || [];
  const inspected = data?.inspectedBackup || null;
  const canManage = currentUser?.role === "admin";

  const backupRows = backups.map((item) => `
    <tr>
      <td>${esc(item.backup_id)}</td>
      <td>${esc(item.created_at)}</td>
      <td>${esc(item.status)}</td>
      <td>${esc(item.record_counts?.total ?? "")}</td>
      <td>${esc(item.file_size_bytes)}</td>
      <td>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="btn secondary" data-inspect-backup="${esc(item.backup_id)}">Inspect</button>
          ${canManage ? `<button class="btn secondary" data-verify-backup="${esc(item.backup_id)}">Verify</button>` : ""}
          ${canManage ? `<button class="btn secondary" data-restore-backup="${esc(item.backup_id)}">Restore</button>` : ""}
        </div>
      </td>
    </tr>
  `).join("");

  const logRows = logs.map((item) => `
    <tr>
      <td>${esc(item.started_at)}</td>
      <td>${esc(item.operation)}</td>
      <td>${esc(item.status)}</td>
      <td>${esc(item.records_processed)}</td>
      <td>${esc(item.error_message || "")}</td>
    </tr>
  `).join("");

  return `
    <section class="grid">
      <h2>Lifecycle & Backups</h2>
      ${message ? `<div class="notice success">${esc(message)}</div>` : ""}
      <div style="display:flex;gap:8px;flex-wrap:wrap;">
        ${canManage ? `<button class="btn" id="create-backup-btn">Creer un backup</button>` : ""}
        <button class="btn secondary" id="refresh-lifecycle-btn">Rafraichir</button>
      </div>
      <div class="grid kpi-grid">
        <article class="card"><div>HOT records</div><div class="kpi-value">${esc(status.hot?.records ?? "-")}</div></article>
        <article class="card"><div>Risky users</div><div class="kpi-value">${esc(status.hot?.risky_users ?? "-")}</div></article>
        <article class="card"><div>Incidents</div><div class="kpi-value">${esc(status.hot?.incidents ?? "-")}</div></article>
        <article class="card"><div>Archive records</div><div class="kpi-value">${esc(status.archive?.records ?? "-")}</div></article>
      </div>
      <article class="card">
        <h3>Backups</h3>
        ${tableOrEmpty(["Backup ID", "Created At", "Status", "Records", "Size", "Action"], backupRows, "Aucun backup")}
      </article>
      <article class="card">
        <h3>Backup Inspector</h3>
        ${inspected ? tableOrEmpty(["File", "Size", "Compressed"], (inspected.entries || []).map((entry) => `
          <tr>
            <td>${esc(entry.name)}</td>
            <td>${esc(entry.size)}</td>
            <td>${esc(entry.compressed_size)}</td>
          </tr>
        `).join(""), "Aucune entree") : `<div class="subtitle">Selectionne un backup via Inspect pour voir son contenu.</div>`}
      </article>
      <article class="card">
        <h3>Lifecycle Logs</h3>
        ${tableOrEmpty(["Started At", "Operation", "Status", "Records", "Error"], logRows, "Aucun log")}
      </article>
    </section>
  `;
}

export function renderDashboard(kpis) {
  const items = [
    ["Connexions", kpis?.total_connexions?.value ?? "-"],
    ["Taux de succès", (kpis?.success_rate?.value != null ? kpis.success_rate.value + "%" : "-")],
    ["Utilisateurs uniques", kpis?.unique_users?.value ?? "-"],
    ["Risky Users", kpis?.risky_users?.value ?? "-"],
    ["Incidents ouverts", kpis?.open_incidents?.value ?? "-"],
    ["Ops critiques", kpis?.critical_ops?.value ?? "-"],
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

  const filters = data?.filters || {};

  return `
    <section class="grid">
      <h2>SignIns</h2>
      <article class="card">
        <h3>Filtres</h3>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px;margin-top:10px;">
          <input class="input" name="signins-user_principal" placeholder="User principal" value="${esc(filters.user_principal || "")}">
          <select class="input" name="signins-status">
            <option value="">Status (tous)</option>
            <option value="success" ${filters.status === "success" ? "selected" : ""}>Success</option>
            <option value="failure" ${filters.status === "failure" ? "selected" : ""}>Failure</option>
          </select>
          <input class="input" type="date" name="signins-date_from" value="${esc(filters.date_from || "")}">
          <input class="input" type="date" name="signins-date_to" value="${esc(filters.date_to || "")}">
        </div>
        <button class="btn" data-apply-filter="signins">Appliquer</button>
      </article>
      ${tableOrEmpty(["Date", "User", "Display Name", "IP", "Status", "App"], rows, "Aucune donnee")}
      ${pager(data?.page, data?.total_pages, "signins")}
    </section>
  `;
}

export function renderAlerts(items, currentUser = null, message = "") {
  const canReview = currentUser?.role === "admin";
  const rows = (items || []).map((a) => `
    <tr>
      <td>${esc(a.user_principal || a.user || "")}</td>
      <td>${esc(a.display_name || "")}</td>
      <td>${esc(a.first_seen || a.timestamp || "")}</td>
      <td>${esc(a.last_seen || "")}</td>
      <td>${esc(a.event_count || "")}</td>
      <td>${esc(a.status || "pending")}</td>
      <td>
        ${canReview && (a.status || "pending") === "pending" ? `
          <div style="display:flex;gap:6px;flex-wrap:wrap;">
            <button class="btn secondary" data-alert-action="approve" data-alert-user="${esc(a.user_principal)}">Approve</button>
            <button class="btn secondary" data-alert-action="reject" data-alert-user="${esc(a.user_principal)}">Reject</button>
          </div>
        ` : ""}
      </td>
    </tr>
  `).join("");

  return `
    <section class="grid">
      <h2>Alertes Nouveaux Utilisateurs</h2>
      ${message ? `<div class="notice success">${esc(message)}</div>` : ""}
      ${tableOrEmpty(["Utilisateur", "Display Name", "First Seen", "Last Seen", "Events", "Status", "Actions"], rows, "Aucune alerte")}
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

  const filters = data?.filters || {};

  return `
    <section class="grid">
      <h2>Risky Users</h2>
      <article class="card">
        <h3>Filtres</h3>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px;margin-top:10px;">
          <input class="input" name="risky-user_principal" placeholder="User principal" value="${esc(filters.user_principal || "")}">
          <select class="input" name="risky-risk_level">
            <option value="">Risk level (tous)</option>
            <option value="high" ${filters.risk_level === "high" ? "selected" : ""}>high</option>
            <option value="medium" ${filters.risk_level === "medium" ? "selected" : ""}>medium</option>
            <option value="low" ${filters.risk_level === "low" ? "selected" : ""}>low</option>
          </select>
        </div>
        <button class="btn" data-apply-filter="risky">Appliquer</button>
      </article>
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

  const filters = data?.filters || {};

  return `
    <section class="grid">
      <h2>Incidents</h2>
      <article class="card">
        <h3>Filtres</h3>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px;margin-top:10px;">
          <input class="input" name="incidents-title_contains" placeholder="Titre contient" value="${esc(filters.title_contains || "")}">
          <select class="input" name="incidents-severity">
            <option value="">Severity (tous)</option>
            <option value="high" ${filters.severity === "high" ? "selected" : ""}>high</option>
            <option value="medium" ${filters.severity === "medium" ? "selected" : ""}>medium</option>
            <option value="low" ${filters.severity === "low" ? "selected" : ""}>low</option>
          </select>
          <input class="input" name="incidents-status" placeholder="Status" value="${esc(filters.status || "")}">
        </div>
        <button class="btn" data-apply-filter="incidents">Appliquer</button>
      </article>
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

  const filters = data?.filters || {};

  return `
    <section class="grid">
      <h2>Audit Logs</h2>
      <article class="card">
        <h3>Filtres</h3>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px;margin-top:10px;">
          <input class="input" name="audit-user_principal" placeholder="User principal" value="${esc(filters.user_principal || "")}">
          <input class="input" name="audit-operation" placeholder="Operation" value="${esc(filters.operation || "")}">
          <input class="input" name="audit-workload" placeholder="Workload" value="${esc(filters.workload || "")}">
        </div>
        <button class="btn" data-apply-filter="audit">Appliquer</button>
      </article>
      ${tableOrEmpty(["Date", "User", "Operation", "Workload", "Resultat"], rows, "Aucune donnee")}
      ${pager(data?.page, data?.total_pages, "audit")}
    </section>
  `;
}

export function renderTruthList(data) {
  const rows = (data?.items || []).map((row) => `
    <tr>
      <td>${esc(row.user_principal)}</td>
      <td>${esc(row.display_name)}</td>
      <td>${esc(row.department)}</td>
      <td>${esc(row.job_title)}</td>
      <td>${row.is_active ? "Active" : "Inactive"}</td>
      <td>${esc(row.imported_by)}</td>
      <td>${esc(row.imported_at)}</td>
      <td>${esc(row.notes)}</td>
    </tr>
  `).join("");

  const filters = data?.filters || {};

  return `
    <section class="grid">
      <h2>Truth List</h2>
      <div class="grid kpi-grid">
        <article class="card"><div>Total utilisateurs</div><div class="kpi-value">${esc(data?.total ?? 0)}</div></article>
        <article class="card"><div>Page</div><div class="kpi-value">${esc(data?.page ?? 1)}</div></article>
      </div>
      <article class="card">
        <h3>Filtres</h3>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px;margin-top:10px;">
          <input class="input" name="truth-user_principal" placeholder="User principal" value="${esc(filters.user_principal || "")}">
          <input class="input" name="truth-department" placeholder="Departement" value="${esc(filters.department || "")}">
          <select class="input" name="truth-is_active">
            <option value="" ${filters.is_active === "" ? "selected" : ""}>Statut (tous)</option>
            <option value="true" ${String(filters.is_active) === "true" ? "selected" : ""}>Actif</option>
            <option value="false" ${String(filters.is_active) === "false" ? "selected" : ""}>Inactif</option>
          </select>
        </div>
        <button class="btn" data-apply-filter="truth">Appliquer</button>
      </article>
      ${tableOrEmpty(["User", "Display Name", "Departement", "Poste", "Statut", "Importe par", "Importe le", "Notes"], rows, "Aucun utilisateur dans la Truth List")}
      ${pager(data?.page, data?.total_pages, "truth")}
    </section>
  `;
}

export function renderSoc(summary, anomalies, filters = {}, message = "") {
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
      <article class="card">
        <h3>Filtres d analyse</h3>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px;margin-top:10px;">
          <select class="input" name="soc-period">
            <option value="today" ${filters.period === "today" ? "selected" : ""}>today</option>
            <option value="last_7_days" ${filters.period === "last_7_days" ? "selected" : ""}>last_7_days</option>
            <option value="last_30_days" ${filters.period === "last_30_days" ? "selected" : ""}>last_30_days</option>
            <option value="custom" ${filters.period === "custom" ? "selected" : ""}>custom</option>
          </select>
          <input class="input" type="date" name="soc-start_date" value="${esc(filters.start_date || "")}">
          <input class="input" type="date" name="soc-end_date" value="${esc(filters.end_date || "")}">
          <input class="input" name="soc-event_type" placeholder="Event type" value="${esc(filters.event_type || "")}">
          <select class="input" name="soc-severity">
            <option value="">Severity (toutes)</option>
            <option value="critical" ${filters.severity === "critical" ? "selected" : ""}>critical</option>
            <option value="high" ${filters.severity === "high" ? "selected" : ""}>high</option>
            <option value="medium" ${filters.severity === "medium" ? "selected" : ""}>medium</option>
            <option value="low" ${filters.severity === "low" ? "selected" : ""}>low</option>
          </select>
          <select class="input" name="soc-status">
            <option value="open" ${filters.status === "open" ? "selected" : ""}>open</option>
            <option value="resolved" ${filters.status === "resolved" ? "selected" : ""}>resolved</option>
            <option value="" ${filters.status === "" ? "selected" : ""}>all</option>
          </select>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <button class="btn" data-apply-filter="soc">Appliquer</button>
          <button class="btn secondary" id="soc-export-html">Exporter HTML</button>
        </div>
      </article>
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
      <td>${esc(u.email || "")}</td>
      <td>${esc(u.role)}</td>
      <td>${esc(u.is_active ? "actif" : "inactif")}</td>
      <td>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="btn secondary" data-update-role="${esc(u.id)}" data-role-target="${u.role === "admin" ? "viewer" : "admin"}" ${currentUser?.id === u.id ? "disabled" : ""}>${u.role === "admin" ? "Passer lecteur" : "Passer admin"}</button>
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
        <h3>Creer un utilisateur</h3>
        <form id="create-reader-form" style="display:grid;gap:10px;">
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:8px;">
            <input class="input" name="username" placeholder="Username" required>
            <input class="input" name="email" type="email" placeholder="Email">
            <input class="input" name="password" type="password" placeholder="Mot de passe" required>
            <select class="input" name="role">
              <option value="viewer" selected>Lecteur</option>
              <option value="admin">Administrateur</option>
            </select>
          </div>
          <div class="subtitle">Le mot de passe doit respecter les regles de securite du backend.</div>
          <div>
            <button class="btn" type="submit">Creer l utilisateur</button>
          </div>
        </form>
      </article>
      <article class="card">
        <h3>Nettoyage rapide</h3>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;">
          <button class="btn secondary" data-clear="signins">Vider SignIns</button>
          <button class="btn secondary" data-clear="risky_users">Vider Risky</button>
          <button class="btn secondary" data-clear="incidents">Vider Incidents</button>
          <button class="btn secondary" data-clear="audit_logs">Vider Audit</button>
        </div>
      </article>
      ${tableOrEmpty(["ID", "Username", "Email", "Role", "Etat", "Actions"], rows, "Aucun utilisateur")}
    </section>
  `;
}
