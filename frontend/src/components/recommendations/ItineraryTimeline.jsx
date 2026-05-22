import { useState } from "react";

function categoryIcon(activity) {
  const kinds = String(activity?.kinds || "").toLowerCase();
  if (kinds.includes("water") || kinds.includes("waterfall")) return "💧";
  if (kinds.includes("cultural") || kinds.includes("temple") || kinds.includes("religion")) return "🛕";
  if (kinds.includes("wildlife") || kinds.includes("park")) return "🦋";
  if (kinds.includes("sport") || kinds.includes("hiking")) return "🥾";
  if (kinds.includes("beach")) return "🏖";
  return "🌿";
}

function SourceBadge({ source }) {
  if (source === "discovered") {
    return (
      <span className="rounded-full bg-stone-200 px-2 py-0.5 text-[10px] font-medium text-stone-600">
        🔍 Discovery
      </span>
    );
  }
  return (
    <span className="rounded-full bg-gold/20 px-2 py-0.5 text-[10px] font-medium text-gold-dark">
      ✓ Verified
    </span>
  );
}

function ActivityImage({ activity, name }) {
  const [loaded, setLoaded] = useState(false);
  const [failed, setFailed] = useState(false);
  const url = activity?.image_url;

  if (!url || failed) {
    return (
      <div
        className="flex h-32 w-full items-center justify-center rounded-t-lg bg-gradient-to-br from-forest to-forest-light text-3xl"
        aria-hidden="true"
      >
        {categoryIcon(activity)}
      </div>
    );
  }

  return (
    <div className="relative h-32 w-full overflow-hidden rounded-t-lg">
      {!loaded && (
        <div
          className="absolute inset-0 animate-pulse bg-cream-dark"
          aria-hidden="true"
        />
      )}
      <img
        src={url}
        alt={name}
        loading="lazy"
        className={`h-32 w-full object-cover transition-opacity duration-300 ${
          loaded ? "opacity-100" : "opacity-0"
        }`}
        onLoad={() => setLoaded(true)}
        onError={() => setFailed(true)}
      />
    </div>
  );
}

function ActivityBlock({ activity, label }) {
  if (!activity) return null;

  const name =
    typeof activity === "string" ? activity : activity.attraction_name || activity.name;
  const description = typeof activity === "object" ? activity.description : "";
  const cost = typeof activity === "object" ? activity.estimated_cost_usd : null;
  const source = typeof activity === "object" ? activity.source : "curated";
  const distanceKm = typeof activity === "object" ? activity.distance_km : null;
  const travelTime =
    typeof activity === "object" ? activity.travel_time_formatted : null;
  const tips = typeof activity === "object" ? activity.tips : null;
  const hasImage = typeof activity === "object" && activity.image_url;

  return (
    <article className="overflow-hidden rounded-lg border border-cream-dark bg-white">
      {(hasImage || source === "discovered") && (
        <ActivityImage activity={typeof activity === "object" ? activity : {}} name={name} />
      )}
      <div className="p-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-gold-dark">
            {label}
          </p>
          <SourceBadge source={source} />
        </div>
        <h4 className="mt-1 text-sm font-semibold text-forest">{name}</h4>
        {(distanceKm != null || travelTime) && (
          <p className="mt-1 text-[11px] text-forest/55">
            📍 {distanceKm != null ? `${distanceKm} km` : ""}
            {distanceKm != null && travelTime ? " · " : ""}
            {travelTime || ""}
          </p>
        )}
        {description && (
          <p className="mt-1 text-xs leading-relaxed text-forest/60">{description}</p>
        )}
        {tips && (
          <p className="mt-1 text-[11px] italic text-forest/50">Tip: {tips}</p>
        )}
        <footer className="mt-2 flex flex-wrap gap-2">
          {cost != null && cost > 0 && (
            <span className="rounded-full bg-gold/15 px-2 py-0.5 text-[10px] font-medium text-gold-dark">
              ~${cost}
            </span>
          )}
        </footer>
      </div>
    </article>
  );
}

function DayColumn({ day }) {
  const evening =
    typeof day.evening === "string"
      ? day.evening
      : day.evening?.attraction_name || day.evening?.description;

  return (
    <li className="relative border-l-2 border-gold/40 pb-8 pl-6 last:pb-0">
      <span className="absolute -left-[9px] top-0 h-4 w-4 rounded-full border-2 border-gold bg-cream" />
      <header className="mb-3">
        <p className="text-xs font-semibold uppercase tracking-wider text-gold-dark">
          Day {day.day_number}
        </p>
        {day.theme && (
          <h3 className="font-display text-sm font-semibold text-forest">{day.theme}</h3>
        )}
        {day.estimated_day_cost_usd > 0 && (
          <p className="text-xs text-forest/50">
            Est. ${day.estimated_day_cost_usd} for activities
          </p>
        )}
      </header>
      <section className="space-y-2">
        <ActivityBlock activity={day.morning} label="Morning" />
        <ActivityBlock activity={day.afternoon} label="Afternoon" />
        {evening && (
          <article className="rounded-lg border border-forest/10 bg-cream-light p-3">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-forest/45">
              Evening
            </p>
            <p className="mt-1 text-xs text-forest/70">{evening}</p>
          </article>
        )}
      </section>
    </li>
  );
}

function ItineraryTimeline({ itinerary }) {
  const days = itinerary?.itinerary || itinerary || [];
  if (!days.length) return null;

  const total = itinerary?.total_estimated_cost_usd;
  const discoveriesUnavailable = itinerary?.discoveries_unavailable;
  const discoveredCount = itinerary?.discovered_count ?? 0;

  return (
    <section>
      <header className="mb-4">
        <h3 className="font-display text-sm font-semibold text-forest">Your itinerary</h3>
        {itinerary?.narrative && (
          <p className="mt-1 text-xs leading-relaxed text-forest/60">{itinerary.narrative}</p>
        )}
        {total > 0 && (
          <p className="mt-2 text-xs font-medium text-gold-dark">
            Total estimated activities: ${total}
          </p>
        )}
        {discoveredCount > 0 && (
          <p className="mt-1 text-[11px] text-forest/50">
            Includes {discoveredCount} nearby discover{discoveredCount === 1 ? "y" : "ies"} from
            OpenTripMap
          </p>
        )}
        {discoveriesUnavailable && (
          <p className="mt-2 rounded-lg border border-cream-dark bg-cream-light px-3 py-2 text-xs text-forest/60">
            Unable to load nearby discoveries right now. Your verified Leafy Cave attractions are
            still included below.
          </p>
        )}
      </header>
      <ol className="m-0 list-none p-0">
        {days.map((day) => (
          <DayColumn key={day.day_number} day={day} />
        ))}
      </ol>
    </section>
  );
}

export default ItineraryTimeline;
