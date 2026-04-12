export const state = {
  token: localStorage.getItem("siem_token") || "",
  user: null,
  activeView: "dashboard",
  pages: {
    signins: 1,
    risky: 1,
    incidents: 1,
    audit: 1,
    soc: 1,
  },
  filters: {
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
  },
};

export function setToken(token) {
  state.token = token || "";
  if (state.token) {
    localStorage.setItem("siem_token", state.token);
  } else {
    localStorage.removeItem("siem_token");
  }
}
