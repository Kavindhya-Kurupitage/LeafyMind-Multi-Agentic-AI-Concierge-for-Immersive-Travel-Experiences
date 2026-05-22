/** Normalize planning agent artifacts from API / SSE (nested or legacy flat). */

export function normalizeThreadArtifacts(raw) {
  if (!raw || typeof raw !== "object") return {};
  const next = { ...raw };

  if (!next.food && (next.must_try?.length || next.narrative)) {
    next.food = {
      must_try: next.must_try,
      safe_starter: next.safe_starter,
      dishes_to_avoid: next.dishes_to_avoid,
      narrative: next.narrative,
    };
  }
  if (!next.packages && next.recommendations?.length) {
    next.packages = {
      recommendations: next.recommendations,
      narrative: next.narrative,
    };
  }
  if (next.itinerary && Array.isArray(next.itinerary)) {
    next.itinerary = {
      itinerary: next.itinerary,
      narrative: next.narrative,
      total_estimated_cost_usd: next.total_estimated_cost_usd,
      curated_count: next.curated_count,
      discovered_count: next.discovered_count,
    };
  }
  return next;
}

export function resolveFoodArtifacts(artifacts) {
  if (!artifacts) return null;
  const normalized = normalizeThreadArtifacts(artifacts);
  const food = normalized.food;
  if (food && (food.must_try?.length || food.narrative)) return food;
  return null;
}

export function resolvePackageList(artifacts) {
  if (!artifacts) return [];
  const normalized = normalizeThreadArtifacts(artifacts);
  return normalized.packages?.recommendations || [];
}

export function resolveItineraryArtifacts(artifacts) {
  if (!artifacts) return null;
  const normalized = normalizeThreadArtifacts(artifacts);
  const block = normalized.itinerary;
  if (!block) return null;
  if (Array.isArray(block) && block.length > 0) {
    return {
      itinerary: block,
      narrative: normalized.narrative,
      total_estimated_cost_usd: normalized.total_estimated_cost_usd,
    };
  }
  if (block.itinerary?.length) return block;
  return null;
}

/** Pull structured outputs from the latest assistant message (legacy threads). */
export function extractArtifactsFromMessages(messages, agentId) {
  const list = messages || [];
  for (let i = list.length - 1; i >= 0; i -= 1) {
    const msg = list[i];
    if (msg.role !== "assistant" || !msg.artifacts) continue;
    const merged = normalizeThreadArtifacts(msg.artifacts);
    if (agentId === "food_guide" && resolveFoodArtifacts(merged)) {
      return { ...merged };
    }
    if (agentId === "package_recommender" && resolvePackageList(merged).length) {
      return { ...merged };
    }
    if (agentId === "itinerary_planner" && resolveItineraryArtifacts(merged)) {
      return { ...merged };
    }
  }
  return {};
}
