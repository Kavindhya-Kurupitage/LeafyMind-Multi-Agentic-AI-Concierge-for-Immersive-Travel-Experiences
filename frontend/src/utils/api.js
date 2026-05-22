/**
 * Axios client for the LeafyMind BFF with auth interceptors.
 */

import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:3002/api";

/** Auth can be slow on Docker Desktop when the API is under memory pressure. */
const AUTH_TIMEOUT_MS = 90_000;

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30_000,
});

let authHandlers = {
  getToken: () => localStorage.getItem("leafymind_token"),
  onUnauthorized: () => {},
};

/**
 * Wire auth token getter and logout handler from AuthProvider.
 */
export function configureApiAuth({ getToken, onUnauthorized }) {
  authHandlers = { getToken, onUnauthorized };
}

api.interceptors.request.use((config) => {
  const token = authHandlers.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      authHandlers.onUnauthorized();
      const path = window.location.pathname;
      if (!path.startsWith("/signin") && !path.startsWith("/register")) {
        window.location.assign("/signin");
      }
    }
    return Promise.reject(error);
  }
);

function getErrorMessage(error) {
  if (error.code === "ECONNABORTED" || /timeout/i.test(error.message || "")) {
    return "The server is slow or still starting. Wait a few seconds and try again.";
  }
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg || d).join(", ");
  return error.response?.data?.message || error.message || "Request failed";
}

const authRequestConfig = { timeout: AUTH_TIMEOUT_MS };

export const authAPI = {
  async login(email, password) {
    const { data } = await api.post(
      "/auth/login",
      { email, password },
      authRequestConfig
    );
    return data;
  },

  async register({ email, password, full_name }) {
    const { data } = await api.post(
      "/auth/register",
      { email, password, full_name },
      authRequestConfig
    );
    return data;
  },

  async me() {
    const { data } = await api.get("/auth/me", authRequestConfig);
    return data;
  },

  async logout() {
    const { data } = await api.post("/auth/logout", null, authRequestConfig);
    return data;
  },
};

function getAuthToken() {
  return localStorage.getItem("leafymind_token");
}

function flushSSEBuffer(buffer, onEvent) {
  const parts = buffer.split("\n\n");
  const remainder = parts.pop() ?? "";
  for (const part of parts) {
    const line = part.trim();
    if (!line.startsWith("data:")) continue;
    try {
      onEvent(JSON.parse(line.replace(/^data:\s*/, "")));
    } catch {
      /* ignore malformed chunks */
    }
  }
  return remainder;
}

/**
 * Stream chat via POST + ReadableStream (SSE). EventSource only supports GET;
 * fetch streaming is used for POST /chat/message.
 */
export async function streamChatMessageEvents(sessionId, message, signal, onEvent) {
  const token = getAuthToken();
  const response = await fetch(`${API_BASE}/chat/message`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ session_id: sessionId, message }),
    signal,
  });

  if (!response.ok) {
    let detail = "Unable to reach the concierge";
    try {
      const err = await response.json();
      detail = err.detail || detail;
    } catch {
      /* default */
    }
    throw new Error(typeof detail === "string" ? detail : "Request failed");
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("Streaming not supported");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    buffer = flushSSEBuffer(buffer, onEvent);
  }

  if (buffer.trim()) {
    flushSSEBuffer(`${buffer}\n\n`, onEvent);
  }
}

export const feedbackAPI = {
  async getSummary() {
    const { data } = await api.get("/feedback/summary");
    return data;
  },

  async getFlagged() {
    const { data } = await api.get("/feedback/flagged");
    return data;
  },

  async toggleFlag(feedbackId) {
    const { data } = await api.post(`/feedback/flag/${feedbackId}`);
    return data;
  },

  async submit(payload) {
    const { data } = await api.post("/feedback/submit", payload);
    return data;
  },
};

/**
 * Stream agent hub messages via POST + ReadableStream (SSE).
 */
export async function streamAgentMessageEvents(threadId, payload, signal, onEvent) {
  const token = getAuthToken();
  const body =
    typeof payload === "string"
      ? { message: payload }
      : {
          message: payload.message ?? "",
          ...(payload.guided_response ? { guided_response: payload.guided_response } : {}),
        };
  const response = await fetch(`${API_BASE}/agents/threads/${threadId}/message`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    let detail = "Unable to reach the agent";
    try {
      const err = await response.json();
      detail = err.detail || detail;
    } catch {
      /* default */
    }
    throw new Error(typeof detail === "string" ? detail : "Request failed");
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("Streaming not supported");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    buffer = flushSSEBuffer(buffer, onEvent);
  }

  if (buffer.trim()) {
    flushSSEBuffer(`${buffer}\n\n`, onEvent);
  }
}

export const tripPackAPI = {
  async getSummary() {
    const { data } = await api.get("/trip-pack/summary");
    return data;
  },

  async downloadPdf(guestName) {
    const response = await api.get("/trip-pack/pdf", { responseType: "blob" });
    const blob = new Blob([response.data], { type: "application/pdf" });
    const slug = (guestName || "Guest").replace(/[^\w\s-]/g, "").trim().replace(/\s+/g, "-") || "Guest";
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `Leafy-Cave-Trip-Plan-${slug}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  },

  async sendEmail(email) {
    const body = email ? { email } : {};
    const { data } = await api.post("/trip-pack/email", body);
    return data;
  },
};

export const agentsAPI = {
  async listAgents() {
    const { data } = await api.get("/agents");
    return data;
  },

  async getJourney() {
    const { data } = await api.get("/agents/journey");
    return data;
  },

  async getAgent(agentId) {
    const { data } = await api.get(`/agents/${agentId}`);
    return data;
  },

  async createThread(agentId, options = {}) {
    const payload = {};
    if (options.title) payload.title = options.title;
    if (options.feedbackSessionId) {
      payload.feedback_session_id = options.feedbackSessionId;
    }
    const { data } = await api.post(
      `/agents/${agentId}/threads`,
      Object.keys(payload).length ? payload : {}
    );
    return data;
  },

  async listThreads(agentId) {
    const { data } = await api.get(`/agents/${agentId}/threads`);
    return data;
  },

  async getThread(threadId) {
    const { data } = await api.get(`/agents/threads/${threadId}`);
    return data;
  },
};

export const chatAPI = {
  async startSession() {
    const { data } = await api.post("/chat/session/start");
    return data;
  },

  async getSession(sessionId) {
    const { data } = await api.get(`/chat/session/${sessionId}`);
    return data;
  },

  async getHistory(sessionId, page = 1) {
    const { data } = await api.get(`/chat/history/${sessionId}`, { params: { page } });
    return data;
  },

  async endSession(sessionId) {
    const { data } = await api.post(`/chat/session/${sessionId}/end`);
    return data;
  },

  async getPackages(sessionId) {
    const { data } = await api.get(`/recommendations/packages/${sessionId}`);
    return data;
  },

  async getItinerary(sessionId) {
    const { data } = await api.get(`/recommendations/itinerary/${sessionId}`);
    return data;
  },

  async getFoodGuide(sessionId) {
    const { data } = await api.get(`/recommendations/food/${sessionId}`);
    return data;
  },
};

export { api, getErrorMessage, API_BASE, getAuthToken };
export default api;
