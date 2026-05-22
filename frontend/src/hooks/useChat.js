import { useCallback, useEffect, useRef, useState } from "react";
import { chatAPI, streamChatMessageEvents } from "../utils/api.js";
import { shouldFetchRecommendations } from "../utils/chatHelpers.js";
import {
  getStoredSessions,
  updateSessionPreview,
  upsertStoredSession,
} from "../utils/sessionsStorage.js";

let messageId = 0;
const nextId = () => ++messageId;

const INITIAL_RECOMMENDATIONS = {
  packages: [],
  food: null,
  itinerary: null,
};

const MAX_RETRIES = 3;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function historyToMessages(historyItems) {
  return (historyItems || []).map((turn) => ({
    id: nextId(),
    role: turn.role === "assistant" ? "assistant" : "user",
    content: turn.content || "",
    agent: turn.agent_used || null,
    isStreaming: false,
  }));
}

/**
 * Manages concierge chat state, SSE streaming, and recommendation panels.
 */
export default function useChat(userId, { autoStart = true } = {}) {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentPhase, setCurrentPhase] = useState("GREETING");
  const [feedbackMode, setFeedbackMode] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [recommendations, setRecommendations] = useState(INITIAL_RECOMMENDATIONS);
  const [pastSessions, setPastSessions] = useState([]);
  const [error, setError] = useState(null);
  const [streamingMessage, setStreamingMessage] = useState(null);

  const abortRef = useRef(null);
  const sessionIdRef = useRef(null);

  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  useEffect(() => {
    if (userId) {
      setPastSessions(getStoredSessions(userId));
    }
  }, [userId]);

  const refreshRecommendations = useCallback(async (sid) => {
    if (!sid) return;
    const next = { ...INITIAL_RECOMMENDATIONS };

    const [pkgRes, foodRes, itinRes] = await Promise.allSettled([
      chatAPI.getPackages(sid),
      chatAPI.getFoodGuide(sid),
      chatAPI.getItinerary(sid),
    ]);

    if (pkgRes.status === "fulfilled") {
      next.packages = pkgRes.value.recommendations || [];
    }
    if (foodRes.status === "fulfilled") {
      next.food = foodRes.value;
    }
    if (itinRes.status === "fulfilled") {
      next.itinerary = itinRes.value;
    }

    setRecommendations(next);
  }, []);

  const startSession = useCallback(async () => {
    setError(null);
    const data = await chatAPI.startSession();
    const id = data.session_id;
    setSessionId(id);
    sessionIdRef.current = id;
    setCurrentPhase("GREETING");
    setMessages([]);
    setStreamingMessage(null);
    setRecommendations(INITIAL_RECOMMENDATIONS);

    if (userId) {
      upsertStoredSession(userId, {
        id,
        createdAt: data.created_at,
        preview: "New conversation",
        status: data.status,
      });
      setPastSessions(getStoredSessions(userId));
    }
    return id;
  }, [userId]);

  const loadHistory = useCallback(async (sid) => {
    if (!sid) return;
    setError(null);
    try {
      const [sessionData, historyData] = await Promise.all([
        chatAPI.getSession(sid),
        chatAPI.getHistory(sid, 1),
      ]);
      setSessionId(sid);
      sessionIdRef.current = sid;
      setCurrentPhase(sessionData.phase || "GREETING");
      setMessages(historyToMessages(historyData.messages));
      setStreamingMessage(null);
      await refreshRecommendations(sid);
    } catch (err) {
      setError(err.message || "Could not load conversation");
    }
  }, [refreshRecommendations]);

  const selectSession = useCallback(
    async (sid) => {
      if (sid === sessionIdRef.current) return;
      if (abortRef.current) {
        abortRef.current.abort();
        abortRef.current = null;
      }
      setIsStreaming(false);
      setFeedbackMode(false);
      await loadHistory(sid);
    },
    [loadHistory]
  );

  const enterFeedbackMode = useCallback(
    async (sid) => {
      if (abortRef.current) {
        abortRef.current.abort();
        abortRef.current = null;
      }
      setIsStreaming(false);
      setFeedbackMode(true);
      setError(null);
      try {
        await loadHistory(sid);
        const sessionData = await chatAPI.getSession(sid);
        if (sessionData.phase !== "FEEDBACK") {
          await chatAPI.endSession(sid);
        }
        setCurrentPhase("FEEDBACK");
        setMessages((prev) => {
          if (prev.length > 0) return prev;
          return [
            {
              id: nextId(),
              role: "assistant",
              content:
                "Ayubowan! We'd love to hear how your stay at Leafy Cave was. " +
                "Your honest feedback helps us welcome future guests even better. " +
                "How was your overall experience?",
              agent: "FeedbackCollectorAgent",
              isStreaming: false,
            },
          ];
        });
      } catch (err) {
        setError(err.message || "Could not open feedback for this stay");
      }
    },
    [loadHistory]
  );

  const sendMessage = useCallback(
    async (text) => {
      const trimmed = text.trim();
      if (!trimmed || isStreaming) return;

      let sid = sessionIdRef.current;
      if (!sid) {
        sid = await startSession();
      }

      const userMessage = { id: nextId(), role: "user", content: trimmed };
      setMessages((prev) => [...prev, userMessage]);
      setIsStreaming(true);
      setError(null);

      if (userId) {
        updateSessionPreview(userId, sid, trimmed);
        setPastSessions(getStoredSessions(userId));
      }

      const assistantId = nextId();
      let accumulated = "";
      let lastAgent = "OrchestratorAgent";
      let lastPhase = currentPhase;

      setStreamingMessage({
        id: assistantId,
        role: "assistant",
        content: "",
        agent: null,
        phase: lastPhase,
        isStreaming: true,
      });

      const runAttempt = async (attempt) => {
        const controller = new AbortController();
        abortRef.current = controller;

        await streamChatMessageEvents(
          sid,
          trimmed,
          controller.signal,
          (event) => {
            if (event.type === "error") {
              throw new Error(event.message || "Something went wrong");
            }
            if (event.type === "done") {
              if (event.session_summary?.phase) {
                lastPhase = event.session_summary.phase;
                setCurrentPhase(lastPhase);
              }
              return;
            }
            if (event.token) {
              accumulated += event.token;
              if (event.agent) lastAgent = event.agent;
              if (event.phase) {
                lastPhase = event.phase;
                setCurrentPhase(event.phase);
              }
              setStreamingMessage({
                id: assistantId,
                role: "assistant",
                content: accumulated,
                agent: lastAgent,
                phase: lastPhase,
                isStreaming: true,
              });
            }
          }
        );
      };

      try {
        let lastError;
        for (let attempt = 0; attempt < MAX_RETRIES; attempt += 1) {
          try {
            if (attempt > 0) {
              accumulated = "";
              await sleep(2 ** attempt * 400);
            }
            await runAttempt(attempt);
            lastError = null;
            break;
          } catch (err) {
            if (err.name === "AbortError") return;
            lastError = err;
          }
        }
        if (lastError) throw lastError;

        const finalMessage = {
          id: assistantId,
          role: "assistant",
          content: accumulated,
          agent: lastAgent,
          phase: lastPhase,
          isStreaming: false,
        };
        setStreamingMessage(null);
        setMessages((prev) => [...prev, finalMessage]);

        if (shouldFetchRecommendations(lastAgent, lastPhase)) {
          await refreshRecommendations(sid);
        }
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message || "Unable to reach the concierge. Please try again.");
          setStreamingMessage(null);
        }
      } finally {
        setIsStreaming(false);
        abortRef.current = null;
      }
    },
    [isStreaming, currentPhase, startSession, userId, refreshRecommendations]
  );

  useEffect(() => {
    if (!userId || !autoStart) return;
    startSession().catch((err) => {
      setError(err.message || "Could not start a new session");
    });
    return () => {
      if (abortRef.current) {
        abortRef.current.abort();
      }
    };
  }, [userId, autoStart]); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    messages,
    isStreaming,
    currentPhase,
    sessionId,
    recommendations,
    pastSessions,
    error,
    streamingMessage,
    startSession,
    sendMessage,
    loadHistory,
    selectSession,
    enterFeedbackMode,
    feedbackMode,
    refreshRecommendations,
    setError,
  };
}
