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
};

export function setToken(token) {
  state.token = token || "";
  if (state.token) {
    localStorage.setItem("siem_token", state.token);
  } else {
    localStorage.removeItem("siem_token");
  }
}
