import FoodGuideCard from "../recommendations/FoodGuideCard.jsx";
import ItineraryTimeline from "../recommendations/ItineraryTimeline.jsx";
import PackageCard from "../recommendations/PackageCard.jsx";
import {
  resolveFoodArtifacts,
  resolveItineraryArtifacts,
  resolvePackageList,
} from "../../utils/agentArtifacts.js";
import { getPhaseLabel } from "../../utils/chatHelpers.js";
import { resolveProfileArtifact } from "../../utils/profileCompleteness.js";

function ProfileArtifactPanel({ data, guestProfile }) {
  const profile = data?.profile || guestProfile || {};
  const completeness = data?.completeness ?? 0;

  const fields = [
    { label: "Travel style", value: profile.travel_style },
    { label: "Group", value: profile.group_type },
    { label: "Budget", value: profile.budget_tier },
    { label: "Nights", value: profile.duration_nights },
    {
      label: "Dietary",
      value: Array.isArray(profile.dietary_restrictions)
        ? profile.dietary_restrictions.join(", ")
        : profile.dietary_restrictions,
    },
    { label: "Email", value: profile.email },
  ];

  return (
    <section className="space-y-4">
      <header className="rounded-xl border border-forest/15 bg-white p-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-forest/50">
          Your travel profile
        </p>
        <ProfileProgress completeness={completeness} />
        <p className="mt-2 text-sm text-forest/70">
          {completeness >= 100
            ? "Profile complete — other agents can personalise fully."
            : "Keep chatting to fill in the remaining details."}
        </p>
      </header>
      <ul className="space-y-2">
        {fields.map(({ label, value }) => (
          <li
            key={label}
            className="flex justify-between gap-2 rounded-lg border border-cream-dark bg-cream-light/50 px-3 py-2 text-sm"
          >
            <span className="text-forest/55">{label}</span>
            <span className="font-medium text-forest">{value || "—"}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function ProfileProgress({ completeness }) {
  return (
    <div className="mt-3">
      <div className="flex justify-between text-xs text-forest/60">
        <span>Completeness</span>
        <span className="font-semibold text-gold-dark">{completeness}%</span>
      </div>
      <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-cream-dark">
        <div
          className="h-full rounded-full bg-gradient-to-r from-forest-light to-gold transition-all duration-500"
          style={{ width: `${Math.min(100, completeness)}%` }}
        />
      </div>
    </div>
  );
}

function ProfileHintPanel({ guestProfile }) {
  const resolved = resolveProfileArtifact({}, guestProfile);
  const p = resolved.profile;
  return (
    <section className="space-y-3 rounded-xl border border-forest/15 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wider text-forest/50">
        Loaded from Profile Builder
      </p>
      <ProfileProgress completeness={resolved.completeness} />
      <ul className="space-y-1.5 text-sm text-forest/75">
        <li>
          <span className="text-forest/50">Stay:</span> {p.duration_nights || "—"} nights
        </li>
        <li>
          <span className="text-forest/50">Group:</span> {p.group_type || "—"}
        </li>
        <li>
          <span className="text-forest/50">Dietary:</span>{" "}
          {Array.isArray(p.dietary_restrictions)
            ? p.dietary_restrictions.join(", ")
            : p.dietary_restrictions || "—"}
        </li>
      </ul>
      <p className="text-xs text-forest/50">
        Answer the specialist&apos;s questions in chat — then tap generate when you are ready.
      </p>
    </section>
  );
}

function AgentArtifactPanel({ agentId, artifacts, guestProfile }) {
  const packages = resolvePackageList(artifacts);
  const food = resolveFoodArtifacts(artifacts);
  const itinerary = resolveItineraryArtifacts(artifacts);
  const profile = artifacts?.profile;
  const journey = artifacts?.journey;

  if (agentId === "profile_builder") {
    const resolved = resolveProfileArtifact(artifacts, guestProfile);
    return <ProfileArtifactPanel data={resolved} guestProfile={guestProfile} />;
  }

  if (agentId === "package_recommender" && packages?.length) {
    return (
      <section className="space-y-3">
        <h3 className="font-display text-sm font-semibold text-forest">Recommended stays</h3>
        {packages.map((pkg) => (
          <PackageCard key={pkg.package_name || pkg.name} pkg={pkg} />
        ))}
      </section>
    );
  }

  if (agentId === "food_guide" && (food?.must_try?.length || food?.narrative)) {
    return <FoodGuideCard food={food} />;
  }

  if (agentId === "itinerary_planner" && itinerary?.itinerary?.length) {
    return <ItineraryTimeline itinerary={itinerary} />;
  }

  const PLANNING_AGENTS = ["package_recommender", "food_guide", "itinerary_planner"];
  if (
    PLANNING_AGENTS.includes(agentId) &&
    guestProfile &&
    Object.keys(guestProfile).length > 0
  ) {
    return <ProfileHintPanel guestProfile={guestProfile} />;
  }

  if (agentId === "concierge" && journey?.phase) {
    return (
      <section className="rounded-xl border border-gold/30 bg-gold/5 p-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-forest/50">
          Journey status
        </p>
        <p className="mt-2 font-display text-lg font-semibold text-forest">
          {getPhaseLabel(journey.phase)}
        </p>
        <p className="mt-2 text-sm text-forest/60">
          The concierge coordinates all specialists in one continuous flow.
        </p>
      </section>
    );
  }

  if (agentId === "feedback_collector" && artifacts?.feedback?.survey_complete) {
    return (
      <p className="rounded-xl border border-forest/20 bg-cream-light p-4 text-sm text-forest/70">
        Thank you — your feedback has been recorded.
      </p>
    );
  }

  return (
    <p className="py-12 text-center text-sm leading-relaxed text-forest/45">
      Outputs from this agent will appear here as you chat — packages, dishes, day plans, or your
      profile summary.
    </p>
  );
}

export default AgentArtifactPanel;
