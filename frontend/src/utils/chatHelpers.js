/** Shared helpers for chat UI labelling and agent detection. */

export const PHASE_LABELS = {
  GREETING: "Welcome to Leafy Cave",
  PROFILING: "Getting to know your preferences",
  CONTACT_COLLECTION: "Saving your itinerary details",
  RECOMMENDING: "Curating your perfect stay, food & adventure",
  ITINERARY: "Mapping your Sri Lanka adventure",
  FOLLOWUP: "Refining your travel plans",
  FEEDBACK: "We would love your feedback",
  ESCALATED: "With our team for personal follow-up",
};

export function getPhaseLabel(phase) {
  const key = (phase || "").toUpperCase().replace(/-/g, "_");
  return PHASE_LABELS[key] || PHASE_LABELS.PROFILING;
}

export function resolveAgentLabel(agentName = "") {
  const lower = agentName.toLowerCase();
  if (lower.includes("profile")) return { label: "Profile", color: "bg-forest-light text-cream" };
  if (lower.includes("package")) return { label: "Package", color: "bg-gold text-forest" };
  if (lower.includes("food")) return { label: "Food", color: "bg-forest-muted text-cream" };
  if (lower.includes("itinerary")) return { label: "Itinerary", color: "bg-forest-dark text-cream" };
  if (lower.includes("feedback")) return { label: "Feedback", color: "bg-cream-dark text-forest" };
  if (lower.includes("concierge")) return { label: "Concierge", color: "bg-forest text-cream" };
  return { label: "Agent", color: "bg-forest text-cream" };
}

export function shouldFetchRecommendations(agent, phase) {
  const a = (agent || "").toLowerCase();
  const p = (phase || "").toUpperCase();
  return (
    p === "RECOMMENDING" ||
    p === "ITINERARY" ||
    p === "CONTACT_COLLECTION" ||
    a.includes("package") ||
    a.includes("food") ||
    a.includes("itinerary") ||
    a.includes("recommending")
  );
}

export function formatSessionDate(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function formatTier(tier) {
  if (!tier) return "Stay";
  return tier.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
