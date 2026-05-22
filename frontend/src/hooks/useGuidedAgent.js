import { useCallback, useState } from "react";

const GUIDED_AGENTS = new Set([
  "profile_builder",
  "package_recommender",
  "food_guide",
  "itinerary_planner",
  "feedback_collector",
]);

export function isGuidedAgent(agentId) {
  return GUIDED_AGENTS.has(agentId);
}

/**
 * Local UI state for the active guided turn (selection + optional text).
 */
export default function useGuidedAgent(initialTurn = null) {
  const [activeTurn, setActiveTurn] = useState(initialTurn);
  const [selection, setSelection] = useState([]);
  const [freeText, setFreeText] = useState("");

  const resetForTurn = useCallback((turn) => {
    setActiveTurn(turn || null);
    setSelection([]);
    setFreeText("");
  }, []);

  const applyTurn = useCallback((turn) => {
    resetForTurn(turn);
  }, [resetForTurn]);

  const buildPayload = useCallback(() => {
    if (!activeTurn) return null;
    return {
      step_id: activeTurn.step_id,
      selected: selection,
      free_text: freeText.trim() || null,
    };
  }, [activeTurn, selection, freeText]);

  return {
    activeTurn,
    selection,
    setSelection,
    freeText,
    setFreeText,
    resetForTurn,
    applyTurn,
    buildPayload,
    setActiveTurn,
  };
}
