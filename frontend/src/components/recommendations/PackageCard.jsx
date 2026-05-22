import { formatTier } from "../../utils/chatHelpers.js";

function PackageCard({ pkg }) {
  const price = pkg.price_per_night_usd ?? pkg.price;
  const inclusions = pkg.inclusions || pkg.includes || [];

  return (
    <article className="rounded-xl border border-cream-dark bg-white p-4 shadow-sm transition hover:shadow-luxury">
      <header className="flex items-start justify-between gap-2">
        <h3 className="font-display text-base font-semibold text-forest">
          {pkg.package_name || pkg.name}
        </h3>
        <div className="flex shrink-0 flex-col items-end gap-1">
          {pkg.honeymoon_recommended && (
            <span className="rounded-full bg-rose-100 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-rose-800">
              Honeymoon pick
            </span>
          )}
          <span className="rounded-full bg-forest px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-cream">
            {formatTier(pkg.tier)}
          </span>
        </div>
      </header>

      {price != null && (
        <p className="mt-2 text-lg font-semibold text-gold-dark">
          ${Number(price).toLocaleString()}
          <span className="text-xs font-normal text-forest/50"> / night</span>
        </p>
      )}

      {pkg.min_nights > 1 && (
        <p className="mt-1 text-xs text-forest/50">Minimum {pkg.min_nights} nights</p>
      )}

      {inclusions.length > 0 && (
        <ul className="mt-3 space-y-1 text-xs text-forest/70">
          {inclusions.map((item) => (
            <li key={item} className="flex gap-2">
              <span className="text-gold">✓</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      )}

      {(pkg.why_this_fits || pkg.fit_reason) && (
        <p className="mt-3 border-t border-cream-dark pt-3 text-sm italic leading-relaxed text-forest-light">
          {pkg.why_this_fits || pkg.fit_reason}
        </p>
      )}

      {pkg.seasonal_note && (
        <p className="mt-2 rounded-lg bg-cream px-3 py-2 text-xs text-forest/60">
          {pkg.seasonal_note}
        </p>
      )}
    </article>
  );
}

export default PackageCard;
