import { useCallback, useEffect, useRef, useState } from "react";
import { agentsAPI, streamAgentMessageEvents } from "../utils/api.js";
import {
  extractArtifactsFromMessages,
  normalizeThreadArtifacts,
  resolvePackageList,
} from "../utils/agentArtifacts.js";
import useGuidedAgent, { isGuidedAgent } from "./useGuidedAgent.js";

let messageId = 0;
const nextId = () => ++messageId;

const PLANNING_TOOLS = new Set(["search_packages", "search_food", "plan_itinerary"]);

function historyToMessages(items) {
  return (items || []).map((turn) => ({
    id: nextId(),
    role: turn.role === "assistant" ? "assistant" : "user",
    content: turn.content || "",
    agent: turn.agent_id || null,
    isStreaming: false,
    guidedTurn: turn.artifacts?.guided_turn || null,
  }));
}

function extractGuidedTurn(detail) {
  if (detail?.guided_turn) return detail.guided_turn;
  const msgs = detail?.messages || [];
  for (let i = msgs.length - 1; i >= 0; i -= 1) {
    const turn = msgs[i].artifacts?.guided_turn;
    if (turn && msgs[i].role === "assistant") return turn;
  }
  return null;
}

/**
 * Manages a single agent thread: messages, artifacts, tool activity, SSE streaming.
 */
export default function useAgentThread(agentId, threadIdProp, options = {}) {
  const { feedbackSessionId } = options;
  const [agentMeta, setAgentMeta] = useState(null);
  const [threadId, setThreadId] = useState(threadIdProp || null);
  const [threads, setThreads] = useState([]);
  const [messages, setMessages] = useState([]);
  const [artifacts, setArtifacts] = useState({});
  const [guestProfile, setGuestProfile] = useState({});
  const [toolActivity, setToolActivity] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [journeyHint, setJourneyHint] = useState(null);
  const [showHistory, setShowHistory] = useState(false);

  const {
    activeTurn,
    selection,
    setSelection,
    freeText,
    setFreeText,
    applyTurn,
    resetForTurn,
    buildPayload,
  } = useGuidedAgent(null);

  const abortRef = useRef(null);
  const threadIdRef = useRef(threadId);
  const guidedMode = isGuidedAgent(agentId);

  useEffect(() => {
    threadIdRef.current = threadId;
  }, [threadId]);

  useEffect(() => {
    setThreadId(threadIdProp || null);
  }, [threadIdProp]);

  const loadAgent = useCallback(async () => {
    if (!agentId) return;
    const meta = await agentsAPI.getAgent(agentId);
    setAgentMeta(meta);
  }, [agentId]);

  const loadThreads = useCallback(async () => {
    if (!agentId) return;
    const list = await agentsAPI.listThreads(agentId);
    setThreads(list);
  }, [agentId]);

  const loadThread = useCallback(
    async (id) => {
      if (!id) return;
      const detail = await agentsAPI.getThread(id);
      setMessages(historyToMessages(detail.messages));
      const fromThread = normalizeThreadArtifacts(detail.artifacts || {});
      const fromMessages = extractArtifactsFromMessages(detail.messages, agentId);
      const merged = normalizeThreadArtifacts({ ...fromThread, ...fromMessages });
      setArtifacts(merged);
      setGuestProfile(detail.guest_profile || {});
      setThreadId(id);
      if (guidedMode) {
        const turn = extractGuidedTurn(detail);
        const hasPlanningOutput =
          resolvePackageList(merged).length > 0 ||
          Boolean(merged.food?.must_try?.length) ||
          Boolean(merged.itinerary?.itinerary?.length);
        if (turn && detail.status === "active" && !hasPlanningOutput) {
          applyTurn(turn);
        } else {
          resetForTurn(null);
        }
      }
    },
    [guidedMode, applyTurn, resetForTurn]
  );

  const startNewThread = useCallback(async () => {
    if (!agentId) return null;
    setError(null);
    const thread = await agentsAPI.createThread(agentId, {
      feedbackSessionId: agentId === "feedback_collector" ? feedbackSessionId : undefined,
    });
    setThreadId(thread.id);
    setMessages([]);
    setArtifacts({});
    setToolActivity([]);
    resetForTurn(null);
    await loadThreads();
    await loadThread(thread.id);
    return thread.id;
  }, [agentId, feedbackSessionId, loadThreads, loadThread, resetForTurn]);

  useEffect(() => {
    let cancelled = false;
    const init = async () => {
      if (!agentId) return;
      setIsLoading(true);
      setError(null);
      try {
        await loadAgent();
        await loadThreads();
        if (threadIdProp) {
          await loadThread(threadIdProp);
        } else {
          const thread = await agentsAPI.createThread(agentId, {
            feedbackSessionId: agentId === "feedback_collector" ? feedbackSessionId : undefined,
          });
          if (!cancelled) {
            setThreadId(thread.id);
            await loadThread(thread.id);
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || "Failed to load agent workspace");
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };
    init();
    return () => {
      cancelled = true;
    };
  }, [agentId, threadIdProp, feedbackSessionId, loadAgent, loadThreads, loadThread]);

  const selectThread = useCallback(
    async (id) => {
      setError(null);
      setIsLoading(true);
      try {
        await loadThread(id);
        await loadThreads();
      } catch (err) {
        setError(err.message || "Could not open conversation");
      } finally {
        setIsLoading(false);
      }
    },
    [loadThread, loadThreads]
  );

  const handleStreamEvent = useCallback(
    (event) => {
      if (event.type === "error") {
        throw new Error(event.message || "Something went wrong");
      }
      if (event.type === "guided_turn" && event.data) {
        applyTurn(event.data);
      }
      if (event.type === "tool_start" && PLANNING_TOOLS.has(event.tool)) {
        resetForTurn(null);
      }
      if (event.type === "token" || event.token) {
        setStreamingMessage((prev) => {
          if (!prev) {
            return {
              id: nextId(),
              role: "assistant",
              content: event.token || "",
              agent: event.agent || agentMeta?.name || agentId,
              isStreaming: true,
            };
          }
          return {
            ...prev,
            content: prev.content + (event.token || ""),
            agent: event.agent || prev.agent,
          };
        });
      } else if (event.type === "tool_start") {
        setToolActivity((prev) => [
          ...prev,
          { id: nextId(), tool: event.tool, label: event.label, status: "running" },
        ]);
      } else if (event.type === "tool_end") {
        setToolActivity((prev) =>
          prev.map((item) =>
            item.tool === event.tool && item.status === "running"
              ? { ...item, status: "done", label: event.label || item.label }
              : item
          )
        );
      } else if (event.type === "artifact") {
        if (event.kind === "profile") {
          setArtifacts((prev) => ({
            ...prev,
            profile: event.data,
          }));
        } else {
          setArtifacts((prev) =>
            normalizeThreadArtifacts({
              ...prev,
              [event.kind]: event.data,
              ...(event.kind === "food" ? event.data : {}),
            })
          );
        }
        if (event.kind === "packages" || event.kind === "food" || event.kind === "itinerary") {
          resetForTurn(null);
        }
      } else if (event.type === "journey" && event.data?.planning_complete) {
        setJourneyHint({
          type: event.data.trip_pack_ready ? "trip_pack_ready" : "planning_progress",
          feedbackEmailSent: Boolean(event.data.feedback_email_sent),
          plannersDoneCount: event.data.planners_done_count ?? 0,
          tripPackReady: Boolean(event.data.trip_pack_ready),
        });
      } else if (event.type === "done" && event.thread) {
        if (event.thread.guest_profile) {
          setGuestProfile(event.thread.guest_profile);
        }
        if (event.thread.artifacts) {
          setArtifacts((prev) =>
            normalizeThreadArtifacts({ ...prev, ...event.thread.artifacts })
          );
        }
        const threadArtifacts = normalizeThreadArtifacts(event.thread.artifacts || {});
        const hasPlanningOutput =
          resolvePackageList(threadArtifacts).length > 0 ||
          Boolean(threadArtifacts.food?.must_try?.length) ||
          Boolean(threadArtifacts.itinerary?.itinerary?.length);

        if (event.thread.guided_turn && event.thread.status === "active") {
          applyTurn(event.thread.guided_turn);
        } else if (event.thread.status !== "active" || hasPlanningOutput) {
          resetForTurn(null);
        }
        if (event.journey?.profile_complete && agentId === "profile_builder") {
          setJourneyHint({ type: "profile_complete" });
        }
      }
    },
    [agentId, agentMeta, applyTurn, resetForTurn]
  );

  const runStream = useCallback(
    async (payload, userLabel) => {
      const tid = threadIdRef.current;
      if (!tid || isStreaming) return;

      setError(null);
      setIsStreaming(true);
      setToolActivity([]);

      const userMsg = {
        id: nextId(),
        role: "user",
        content: userLabel || (typeof payload === "string" ? payload : "Continue"),
        agent: null,
        isStreaming: false,
      };
      setMessages((prev) => [...prev, userMsg]);

      const streamId = nextId();
      const willStreamTokens = typeof payload === "string";
      if (willStreamTokens) {
        setStreamingMessage({
          id: streamId,
          role: "assistant",
          content: "",
          agent: agentMeta?.name || agentId,
          isStreaming: true,
        });
      }

      abortRef.current?.abort();
      abortRef.current = new AbortController();

      try {
        await streamAgentMessageEvents(
          tid,
          payload,
          abortRef.current.signal,
          handleStreamEvent
        );

        setStreamingMessage((prev) => {
          if (prev?.content) {
            setMessages((msgs) => [
              ...msgs,
              {
                id: streamId,
                role: "assistant",
                content: prev.content,
                agent: prev.agent,
                isStreaming: false,
              },
            ]);
          }
          return null;
        });
        await loadThreads();
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message || "Failed to send message");
        }
        setStreamingMessage(null);
      } finally {
        setIsStreaming(false);
        setToolActivity((prev) =>
          prev.map((item) =>
            item.status === "running"
              ? { ...item, status: "done", label: item.label?.replace(/…$/, "") || item.label }
              : item
          )
        );
      }
    },
    [agentMeta, agentId, isStreaming, loadThreads, handleStreamEvent]
  );

  const sendMessage = useCallback(
    async (text) => {
      if (!text.trim()) return;
      await runStream(text.trim(), text.trim());
    },
    [runStream]
  );

  const submitGuided = useCallback(async () => {
    const guidedPayload = buildPayload();
    if (!guidedPayload) return;
    const label =
      selection.length > 0 ? selection.join(", ") : freeText.trim() || "Continue";
    await runStream(
      {
        message: label,
        guided_response: guidedPayload,
      },
      label
    );
  }, [buildPayload, selection, freeText, runStream]);

  const skipGuided = useCallback(async () => {
    if (!activeTurn) return;
    await runStream(
      {
        message: "Skip",
        guided_response: {
          step_id: activeTurn.step_id,
          selected: ["skip"],
          free_text: null,
        },
      },
      "Skip"
    );
  }, [activeTurn, runStream]);

  return {
    agentMeta,
    threadId,
    threads,
    messages,
    artifacts,
    guestProfile,
    toolActivity,
    isStreaming,
    streamingMessage,
    error,
    isLoading,
    sendMessage,
    submitGuided,
    skipGuided,
    startNewThread,
    selectThread,
    setError,
    journeyHint,
    clearJourneyHint: () => setJourneyHint(null),
    guidedMode,
    activeTurn,
    selection,
    setSelection,
    freeText,
    setFreeText,
    showHistory,
    setShowHistory,
  };
}
