/**
 * Mirror backend profile completeness for the hub profile panel.
 */

const REQUIRED_FIELDS = [
  "travel_style",
  "group_type",
  "budget_tier",
  "dietary_restrictions",
  "duration_nights",
];

function fieldFilled(profile, key) {
  const value = profile?.[key];
  if (key === "dietary_restrictions") {
    return value !== undefined && value !== null;
  }
  return value !== undefined && value !== null && value !== "";
}

export function computeProfileCompleteness(profile) {
  if (!profile || typeof profile !== "object") return 0;
  const filled = REQUIRED_FIELDS.filter((key) => fieldFilled(profile, key)).length;
  if (filled === REQUIRED_FIELDS.length) return 100;
  return Math.round((filled / REQUIRED_FIELDS.length) * 100);
}

/**
 * Normalize profile artifact bucket from SSE or thread context.
 */
export function resolveProfileArtifact(artifacts, guestProfile) {
  const bucket = artifacts?.profile;
  if (bucket && typeof bucket === "object") {
    const fields = bucket.profile ?? bucket;
    const completeness =
      bucket.completeness ?? computeProfileCompleteness(fields);
    return {
      profile: fields,
      completeness,
      is_complete: bucket.is_complete ?? completeness >= 100,
    };
  }
  if (artifacts?.completeness !== undefined) {
    return {
      profile: artifacts.profile ?? guestProfile,
      completeness: artifacts.completeness,
      is_complete: artifacts.is_complete ?? artifacts.completeness >= 100,
    };
  }
  return {
    profile: guestProfile || {},
    completeness: computeProfileCompleteness(guestProfile),
    is_complete: computeProfileCompleteness(guestProfile) >= 100,
  };
}
