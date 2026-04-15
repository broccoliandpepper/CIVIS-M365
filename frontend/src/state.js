function createPages() {
  return {
    signins: 1,
    risky: 1,
    incidents: 1,
    audit: 1,
    truth: 1,
    soc: 1,
  };
}

function createFilters() {
  return {
    signins: {
      user_principal: "",
      status: "",
      date_from: "",
      date_to: "",
    },
    risky: {
      user_principal: "",
      risk_level: "",
    },
    incidents: {
      severity: "",
      status: "",
      title_contains: "",
    },
    audit: {
      user_principal: "",
      operation: "",
      workload: "",
    },
    truth: {
      user_principal: "",
      department: "",
      is_active: "",
    },
    soc: {
      period: "last_7_days",
      start_date: "",
      end_date: "",
      event_type: "",
      severity: "",
      status: "open",
    },
  };
}

export const state = {
  token: localStorage.getItem("siem_token") || "",
  user: null,
  activeView: "dashboard",
  pages: createPages(),
  filters: createFilters(),
};

export function setToken(token) {
  state.token = token || "";
  if (state.token) {
    localStorage.setItem("siem_token", state.token);
  } else {
    localStorage.removeItem("siem_token");
  }
}

export function resetSessionState() {
  setToken("");
  state.user = null;
  state.activeView = "dashboard";
  state.pages = createPages();
  state.filters = createFilters();
}
