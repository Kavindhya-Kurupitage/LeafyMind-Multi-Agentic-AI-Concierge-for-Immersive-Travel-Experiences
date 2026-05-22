/**
 * Persist chat session metadata locally (until a list-sessions API exists).
 */

const STORAGE_PREFIX = "leafymind_sessions";

function storageKey(userId) {
  return `${STORAGE_PREFIX}_${userId}`;
}

export function getStoredSessions(userId) {
  if (!userId) return [];
  try {
    const raw = localStorage.getItem(storageKey(userId));
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function upsertStoredSession(userId, session) {
  if (!userId || !session?.id) return;
  const sessions = getStoredSessions(userId);
  const idx = sessions.findIndex((s) => s.id === session.id);
  const entry = {
    id: session.id,
    createdAt: session.createdAt || new Date().toISOString(),
    preview: session.preview || "New conversation",
    status: session.status || "active",
  };
  if (idx >= 0) {
    sessions[idx] = { ...sessions[idx], ...entry };
  } else {
    sessions.unshift(entry);
  }
  localStorage.setItem(storageKey(userId), JSON.stringify(sessions.slice(0, 50)));
}

export function updateSessionPreview(userId, sessionId, preview) {
  const sessions = getStoredSessions(userId);
  const entry = sessions.find((s) => s.id === sessionId);
  if (entry && (!entry.preview || entry.preview === "New conversation")) {
    upsertStoredSession(userId, {
      id: sessionId,
      createdAt: entry.createdAt,
      preview: preview.slice(0, 60),
      status: entry.status,
    });
  }
}
