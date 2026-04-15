import {
  apiApproveUnknownUser,
  apiAuditLogs,
  apiClearData,
  apiCreateBackup,
  apiHealth,
  apiIncidents,
  apiInspectBackup,
  apiKpis,
  apiLifecycleBackups,
  apiLifecycleLogs,
  apiLifecycleStatus,
  apiLogin,
  apiLogout,
  apiMe,
  apiRejectUnknownUser,
  apiResetPassword,
  apiRestoreBackup,
  apiRiskyUsers,
  apiSignins,
  apiSocAnomalies,
  apiSocAnalyze,
  apiSocExportHtml,
  apiSocSummary,
  apiTruthList,
  apiToggleUser,
  apiUnknownUsers,
  apiUpload,
  apiUsers,
  apiVerifyBackup,
} from "./api.js";
import { resetSessionState, setToken, state } from "./state.js";
import {
  renderAdmin,
  renderAlerts,
  renderAppShell,
  renderAuditLogs,
  renderDashboard,
  renderIncidents,
  renderIngestion,
  renderLifecycle,
  renderLogin,
  renderRiskyUsers,
  renderSignins,
  renderSoc,
  renderTruthList,
} from "./views.js";

const app = document.getElementById("app");

function showLogin(error = "") {
  app.innerHTML = renderLogin(error);
  bindLoginForm();
}

async function logoutAndReturnToLogin(error = "") {
  resetSessionState();
  showLogin(error);
}

function setActiveNav() {
  document.querySelectorAll(".nav-btn").forEach((el) => {
    if (el.dataset.view === state.activeView) {
      el.classList.add("active");
    } else {
      el.classList.remove("active");
    }
  });
}

function wirePager(content) {
  content.querySelectorAll("[data-page-action]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const view = btn.dataset.pageView;
      const action = btn.dataset.pageAction;
      if (!view || !action) return;

      const current = state.pages[view] || 1;
      const nextPage = action === "next" ? current + 1 : Math.max(1, current - 1);
      state.pages[view] = nextPage;
      await renderContent();
    });
  });
}

function wireFilters(content) {
  content.querySelectorAll("[data-apply-filter]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const view = btn.dataset.applyFilter;
      if (!view || !state.filters[view]) return;

      Object.keys(state.filters[view]).forEach((key) => {
        const input = content.querySelector(`[name="${view}-${key}"]`);
        state.filters[view][key] = input ? input.value : "";
      });

      if (state.pages[view] !== undefined) {
        state.pages[view] = 1;
      }

      await renderContent();
    });
  });
}

async function wireIngestion(content) {
  content.querySelectorAll("[data-upload]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const fileId = btn.dataset.fileId;
      const input = document.getElementById(fileId);
      const file = input?.files?.[0];
      if (!file) {
        content.innerHTML = renderIngestion("Selectionne un fichier avant l envoi");
        await bindAppHandlers();
        return;
      }

      try {
        const response = await apiUpload(btn.dataset.upload, file);
        content.innerHTML = renderIngestion(response?.message || "Upload termine");
        await bindAppHandlers();
      } catch (error) {
        content.innerHTML = `${renderIngestion()}<div class="notice error">${error.message}</div>`;
        await bindAppHandlers();
      }
    });
  });
}

async function wireSoc(content) {
  document.getElementById("soc-run-analysis")?.addEventListener("click", async () => {
    try {
      const result = await apiSocAnalyze(state.filters.soc);
      const summary = await apiSocSummary(state.filters.soc);
      const anomalies = await apiSocAnomalies(state.filters.soc, state.pages.soc, 50);
      content.innerHTML = renderSoc(summary, anomalies, state.filters.soc, result?.message || "Analyse terminee");
      await bindAppHandlers();
    } catch (error) {
      content.innerHTML = `${renderSoc({}, [], state.filters.soc)}<div class="notice error">${error.message}</div>`;
      await bindAppHandlers();
    }
  });

  document.getElementById("soc-export-html")?.addEventListener("click", async () => {
    try {
      const response = await apiSocExportHtml(state.filters.soc);
      const html = response?.html || "";
      const blob = new Blob([html], { type: "text/html;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `soc-report-${state.filters.soc.period || "period"}.html`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (error) {
      content.innerHTML = `${content.innerHTML}<div class="notice error">${error.message}</div>`;
    }
  });

  wireFilters(content);
  wirePager(content);
}

async function wireAdmin(content) {
  content.querySelectorAll("[data-clear]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        const result = await apiClearData(btn.dataset.clear);
        const users = await apiUsers();
        content.innerHTML = renderAdmin(users, `${btn.dataset.clear}: ${result.deleted} lignes supprimees`, state.user);
        await bindAppHandlers();
      } catch (error) {
        const users = await apiUsers().catch(() => []);
        content.innerHTML = `${renderAdmin(users, "", state.user)}<div class="notice error">${error.message}</div>`;
        await bindAppHandlers();
      }
    });
  });

  content.querySelectorAll("[data-toggle-user]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await apiToggleUser(Number(btn.dataset.toggleUser), btn.dataset.toggleTarget === "true");
        const users = await apiUsers();
        content.innerHTML = renderAdmin(users, "Utilisateur mis a jour", state.user);
        await bindAppHandlers();
      } catch (error) {
        const users = await apiUsers().catch(() => []);
        content.innerHTML = `${renderAdmin(users, "", state.user)}<div class="notice error">${error.message}</div>`;
        await bindAppHandlers();
      }
    });
  });

  content.querySelectorAll("[data-reset-user]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const newPassword = window.prompt("Nouveau mot de passe (min 12 caracteres)");
      if (!newPassword) return;

      try {
        await apiResetPassword(Number(btn.dataset.resetUser), newPassword);
        const users = await apiUsers();
        content.innerHTML = renderAdmin(users, "Mot de passe reinitialise", state.user);
        await bindAppHandlers();
      } catch (error) {
        const users = await apiUsers().catch(() => []);
        content.innerHTML = `${renderAdmin(users, "", state.user)}<div class="notice error">${error.message}</div>`;
        await bindAppHandlers();
      }
    });
  });
}

async function wireAlerts(content) {
  content.querySelectorAll("[data-alert-action]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const action = btn.dataset.alertAction;
      const userPrincipal = btn.dataset.alertUser;
      if (!action || !userPrincipal) return;

      const notes = window.prompt(`Notes pour ${action} ${userPrincipal}`, "") || "";

      try {
        if (action === "approve") {
          await apiApproveUnknownUser(userPrincipal, notes);
        } else {
          await apiRejectUnknownUser(userPrincipal, notes);
        }

        const data = await apiUnknownUsers(50);
        content.innerHTML = renderAlerts(data.items || [], state.user, `Utilisateur ${action === "approve" ? "approuve" : "rejete"}`);
        await bindAppHandlers();
      } catch (error) {
        const data = await apiUnknownUsers(50).catch(() => ({ items: [] }));
        content.innerHTML = `${renderAlerts(data.items || [], state.user)}<div class="notice error">${error.message}</div>`;
        await bindAppHandlers();
      }
    });
  });
}

async function wireLifecycle(content) {
  const reloadLifecycle = async (message = "", inspectedBackup = null) => {
    const status = await apiLifecycleStatus();
    const backups = await apiLifecycleBackups(20);
    const logs = await apiLifecycleLogs(20);
    content.innerHTML = renderLifecycle(
      { status, backups: backups.backups || [], logs: logs.logs || [], inspectedBackup },
      state.user,
      message
    );
    await bindAppHandlers();
  };

  document.getElementById("refresh-lifecycle-btn")?.addEventListener("click", async () => {
    await reloadLifecycle();
  });

  document.getElementById("create-backup-btn")?.addEventListener("click", async () => {
    try {
      const result = await apiCreateBackup();
      await reloadLifecycle(`Backup ${result.status}`);
    } catch (error) {
      content.innerHTML = `${content.innerHTML}<div class="notice error">${error.message}</div>`;
    }
  });

  content.querySelectorAll("[data-inspect-backup]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        const inspected = await apiInspectBackup(btn.dataset.inspectBackup);
        await reloadLifecycle(`Inspection: ${btn.dataset.inspectBackup}`, inspected);
      } catch (error) {
        content.innerHTML = `${content.innerHTML}<div class="notice error">${error.message}</div>`;
      }
    });
  });

  content.querySelectorAll("[data-verify-backup]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        const result = await apiVerifyBackup(btn.dataset.verifyBackup);
        await reloadLifecycle(`Verification: ${result.status}`);
      } catch (error) {
        content.innerHTML = `${content.innerHTML}<div class="notice error">${error.message}</div>`;
      }
    });
  });

  content.querySelectorAll("[data-restore-backup]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        const result = await apiRestoreBackup(btn.dataset.restoreBackup);
        await reloadLifecycle(`Restauration: ${result.status} (${result.restore_path || btn.dataset.restoreBackup})`);
      } catch (error) {
        content.innerHTML = `${content.innerHTML}<div class="notice error">${error.message}</div>`;
      }
    });
  });
}

async function renderContent() {
  const content = document.getElementById("content");
  if (!content) return;

  try {
    if (state.activeView === "dashboard") {
      const data = await apiKpis(30);
      content.innerHTML = renderDashboard(data.kpis || data);
      document.getElementById("refresh-kpi")?.addEventListener("click", () => renderContent());
      return;
    }

    if (state.activeView === "ingestion") {
      content.innerHTML = renderIngestion();
      await wireIngestion(content);
      return;
    }

    if (state.activeView === "signins") {
      const data = await apiSignins(state.pages.signins, 30, state.filters.signins);
      content.innerHTML = renderSignins({ ...data, filters: state.filters.signins });
      wirePager(content);
      wireFilters(content);
      return;
    }

    if (state.activeView === "risky") {
      const data = await apiRiskyUsers(state.pages.risky, 30, state.filters.risky);
      content.innerHTML = renderRiskyUsers({ ...data, filters: state.filters.risky });
      wirePager(content);
      wireFilters(content);
      return;
    }

    if (state.activeView === "incidents") {
      const data = await apiIncidents(state.pages.incidents, 30, state.filters.incidents);
      content.innerHTML = renderIncidents({ ...data, filters: state.filters.incidents });
      wirePager(content);
      wireFilters(content);
      return;
    }

    if (state.activeView === "audit") {
      const data = await apiAuditLogs(state.pages.audit, 30, state.filters.audit);
      content.innerHTML = renderAuditLogs({ ...data, filters: state.filters.audit });
      wirePager(content);
      wireFilters(content);
      return;
    }

    if (state.activeView === "truth") {
      const data = await apiTruthList(state.pages.truth, 30, state.filters.truth);
      content.innerHTML = renderTruthList({ ...data, filters: state.filters.truth });
      wirePager(content);
      wireFilters(content);
      return;
    }

    if (state.activeView === "soc") {
      const summary = await apiSocSummary(state.filters.soc);
      const anomalies = await apiSocAnomalies(state.filters.soc, state.pages.soc, 50);
      content.innerHTML = renderSoc(summary, anomalies, state.filters.soc);
      await wireSoc(content);
      return;
    }

    if (state.activeView === "alerts") {
      const data = await apiUnknownUsers(50);
      content.innerHTML = renderAlerts(data.items || [], state.user);
      await wireAlerts(content);
      return;
    }

    if (state.activeView === "lifecycle") {
      if (state.user?.role !== "admin") {
        content.innerHTML = `<div class="notice error">Section reservee aux admins</div>`;
        return;
      }
      const status = await apiLifecycleStatus();
      const backups = await apiLifecycleBackups(20);
      const logs = await apiLifecycleLogs(20);
      content.innerHTML = renderLifecycle({ status, backups: backups.backups || [], logs: logs.logs || [] }, state.user);
      await wireLifecycle(content);
      return;
    }

    if (state.activeView === "admin") {
      if (state.user?.role !== "admin") {
        content.innerHTML = `<div class="notice error">Section reservee aux admins</div>`;
        return;
      }
      const users = await apiUsers();
      content.innerHTML = renderAdmin(users, "", state.user);
      await wireAdmin(content);
      return;
    }
  } catch (error) {
    content.innerHTML = `<div class="notice error">${error.message}</div>`;
  }
}

async function bindAppHandlers() {
  document.getElementById("logout-btn")?.addEventListener("click", async () => {
    try {
      await apiLogout();
    } catch {
      // Ignore backend logout failures and clear the local session anyway.
    }
    await logoutAndReturnToLogin();
  });

  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      state.activeView = btn.dataset.view;
      setActiveNav();
      await renderContent();
    });
  });

  await renderContent();
}

function bindLoginForm() {
  const form = document.getElementById("login-form");
  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    const username = formData.get("username");
    const password = formData.get("password");

    try {
      const auth = await apiLogin(username, password);
      setToken(auth.access_token);
      await boot();
    } catch (error) {
        showLogin(error.message);
    }
  });
}

async function boot() {
  try {
    await apiHealth();
  } catch {
    app.innerHTML = `<div class="login-shell"><div class="login-card"><div class="notice error">API indisponible</div></div></div>`;
    return;
  }

  if (!state.token) {
    showLogin();
    return;
  }

  try {
    const user = await apiMe();
    state.user = user;
    app.innerHTML = renderAppShell(user);
    setActiveNav();
    await bindAppHandlers();
  } catch {
    await logoutAndReturnToLogin("Session expiree. Reconnecte-toi.");
  }
}

window.addEventListener("siem:unauthorized", () => {
  showLogin("Session expiree. Reconnecte-toi.");
});

boot();
