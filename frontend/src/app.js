import {
  apiHealth,
  apiIncidents,
  apiAuditLogs,
  apiKpis,
  apiLogin,
  apiMe,
  apiRiskyUsers,
  apiSocAnomalies,
  apiSocAnalyze,
  apiSocSummary,
  apiSignins,
  apiResetPassword,
  apiToggleUser,
  apiUnknownUsers,
  apiUsers,
  apiClearData,
  apiUpload,
} from "./api.js";
import { setToken, state } from "./state.js";
import {
  renderAlerts,
  renderAdmin,
  renderAppShell,
  renderAuditLogs,
  renderDashboard,
  renderIncidents,
  renderIngestion,
  renderLogin,
  renderRiskyUsers,
  renderSignins,
  renderSoc,
} from "./views.js";

const app = document.getElementById("app");

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
        const msg = response?.message || "Upload termine";
        content.innerHTML = renderIngestion(msg);
        await bindAppHandlers();
      } catch (error) {
        content.innerHTML = `${renderIngestion()}<div class="notice error">${error.message}</div>`;
        await bindAppHandlers();
      }
    });
  });
}

async function wireSoc(content) {
  const runBtn = document.getElementById("soc-run-analysis");
  if (!runBtn) return;

  runBtn.addEventListener("click", async () => {
    try {
      const result = await apiSocAnalyze("last_7_days");
      const summary = await apiSocSummary("last_7_days");
      const anomalies = await apiSocAnomalies("last_7_days", 1, 50);
      content.innerHTML = renderSoc(summary, anomalies, result?.message || "Analyse terminee");
      await bindAppHandlers();
    } catch (error) {
      content.innerHTML = `${renderSoc({}, [])}<div class="notice error">${error.message}</div>`;
      await bindAppHandlers();
    }
  });

  wirePager(content);
}

async function wireAdmin(content) {
  content.querySelectorAll("[data-clear]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        const source = btn.dataset.clear;
        const result = await apiClearData(source);
        const users = await apiUsers();
        content.innerHTML = renderAdmin(users, `${source}: ${result.deleted} lignes supprimees`, state.user);
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
        const userId = Number(btn.dataset.toggleUser);
        const isActive = btn.dataset.toggleTarget === "true";
        await apiToggleUser(userId, isActive);
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
      const userId = Number(btn.dataset.resetUser);
      const newPassword = window.prompt("Nouveau mot de passe (min 12 caracteres)");
      if (!newPassword) return;

      try {
        await apiResetPassword(userId, newPassword);
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

    if (state.activeView === "soc") {
      const summary = await apiSocSummary("last_7_days");
      const anomalies = await apiSocAnomalies("last_7_days", state.pages.soc, 50);
      content.innerHTML = renderSoc(summary, anomalies);
      await wireSoc(content);
      return;
    }

    if (state.activeView === "alerts") {
      const data = await apiUnknownUsers(50);
      content.innerHTML = renderAlerts(data.items || data || []);
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
  document.getElementById("logout-btn")?.addEventListener("click", () => {
    setToken("");
    state.user = null;
    boot();
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
      app.innerHTML = renderLogin(error.message);
      bindLoginForm();
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
    app.innerHTML = renderLogin();
    bindLoginForm();
    return;
  }

  try {
    const user = await apiMe();
    state.user = user;
    app.innerHTML = renderAppShell(user);
    setActiveNav();
    await bindAppHandlers();
  } catch {
    setToken("");
    app.innerHTML = renderLogin("Session expiree. Reconnecte-toi.");
    bindLoginForm();
  }
}

boot();
