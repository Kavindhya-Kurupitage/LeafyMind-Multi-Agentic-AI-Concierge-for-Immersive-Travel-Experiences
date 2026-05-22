import FoodGuideCard from "../recommendations/FoodGuideCard.jsx";
import ItineraryTimeline from "../recommendations/ItineraryTimeline.jsx";
import PackageCard from "../recommendations/PackageCard.jsx";

function InfoPanel({ recommendations, isOpen, onToggle }) {
  const { packages, food, itinerary } = recommendations;
  const hasContent =
    (packages?.length ?? 0) > 0 || food || (itinerary?.itinerary?.length ?? 0) > 0;

  return (
    <aside
      className={`flex shrink-0 flex-col border-l border-cream-dark bg-cream-light transition-all duration-300 ${
        isOpen ? "w-72 lg:w-[280px]" : "w-0 overflow-hidden border-l-0 lg:w-12"
      }`}
    >
      <header className="flex items-center justify-between border-b border-cream-dark px-4 py-3">
        {isOpen && (
          <h2 className="text-xs font-semibold uppercase tracking-wider text-forest/50">
            Your plan
          </h2>
        )}
        <button
          type="button"
          onClick={onToggle}
          className="ml-auto rounded-lg p-2 text-forest/60 transition hover:bg-cream-dark hover:text-forest"
          aria-label={isOpen ? "Collapse panel" : "Expand panel"}
        >
          {isOpen ? "→" : "←"}
        </button>
      </header>

      {isOpen && (
        <section className="flex-1 overflow-y-auto p-4">
          {!hasContent && (
            <p className="py-8 text-center text-sm leading-relaxed text-forest/45">
              Recommendations will appear here as LeafyMind learns your preferences.
            </p>
          )}

          {packages?.length > 0 && (
            <section className="mb-6">
              <h3 className="mb-3 font-display text-sm font-semibold text-forest">
                Recommended stays
              </h3>
              <section className="space-y-3">
                {packages.map((pkg) => (
                  <PackageCard key={pkg.package_id || pkg.name} pkg={pkg} />
                ))}
              </section>
            </section>
          )}

          {food && (
            <section className="mb-6">
              <FoodGuideCard food={food} />
            </section>
          )}

          {itinerary && (itinerary.itinerary?.length > 0 || Array.isArray(itinerary)) && (
            <ItineraryTimeline itinerary={itinerary} />
          )}
        </section>
      )}
    </aside>
  );
}

export default InfoPanel;
