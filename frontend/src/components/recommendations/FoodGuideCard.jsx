import { useState } from "react";

function spiceIcons(level) {
  const map = { mild: 1, medium: 2, hot: 3, extra_hot: 4 };
  const count = map[String(level || "medium").toLowerCase()] ?? 2;
  return "🌶".repeat(count);
}

function dishKey(dish) {
  if (typeof dish === "string") return dish;
  return dish.dish_name || dish.name || "dish";
}

function dishName(dish) {
  if (typeof dish === "string") return dish;
  return dish.dish_name || dish.name || "";
}

function DishImage({ image, dishLabel }) {
  const [loaded, setLoaded] = useState(false);
  const [failed, setFailed] = useState(false);

  const showPlaceholder = !image?.url || failed;

  if (showPlaceholder) {
    return (
      <div
        className="flex h-40 w-full items-center justify-center rounded-lg bg-cream text-4xl"
        aria-hidden="true"
      >
        🍛
      </div>
    );
  }

  return (
    <figure className="relative overflow-hidden rounded-lg">
      {!loaded && (
        <div
          className="absolute inset-0 animate-pulse rounded-lg bg-cream-dark"
          aria-hidden="true"
        />
      )}
      <img
        src={image.url}
        alt={image.alt_text || dishLabel}
        loading="lazy"
        className={`h-40 w-full object-cover transition-opacity duration-300 ${
          loaded ? "opacity-100" : "opacity-0"
        }`}
        onLoad={() => setLoaded(true)}
        onError={() => setFailed(true)}
      />
      {image.source === "unsplash" && image.photographer && image.unsplash_link && (
        <figcaption className="mt-1.5 text-[10px] leading-snug text-forest/45">
          Photo by{" "}
          <a
            href={image.unsplash_link}
            target="_blank"
            rel="noopener noreferrer"
            className="underline decoration-forest/25 hover:text-forest/70"
          >
            {image.photographer}
          </a>{" "}
          on{" "}
          <a
            href="https://unsplash.com"
            target="_blank"
            rel="noopener noreferrer"
            className="underline decoration-forest/25 hover:text-forest/70"
          >
            Unsplash
          </a>
        </figcaption>
      )}
    </figure>
  );
}

function DishCard({ dish, highlighted }) {
  const name = dishName(dish);
  const spice =
    typeof dish === "object" ? dish.spice_level : null;
  const dietary =
    typeof dish === "object"
      ? dish.dietary_tags || dish.dietary || []
      : [];
  const description =
    typeof dish === "object"
      ? dish.description_plain_english || dish.description || dish.plain_description
      : null;
  const image = typeof dish === "object" ? dish.image : null;

  return (
    <article
      className={`overflow-hidden rounded-lg border ${
        highlighted
          ? "border-gold bg-gold/5 shadow-gold"
          : "border-cream-dark bg-cream-light"
      }`}
    >
      <div className="p-3">
        <DishImage image={image} dishLabel={name} />
      </div>
      <div className="space-y-2 px-3 pb-3">
        <header className="flex items-center justify-between gap-2">
          <h4 className="text-sm font-semibold text-forest">{name}</h4>
          {spice && (
            <span className="text-xs" title={`Spice: ${spice}`}>
              {spiceIcons(spice)}
            </span>
          )}
        </header>
        {dietary?.length > 0 && (
          <p className="flex flex-wrap gap-1">
            {dietary.map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-forest/10 px-2 py-0.5 text-[10px] uppercase text-forest/70"
              >
                {tag}
              </span>
            ))}
          </p>
        )}
        {description && (
          <p className="text-xs leading-relaxed text-forest/65">{description}</p>
        )}
      </div>
    </article>
  );
}

function FoodGuideCard({ food }) {
  if (!food) return null;

  const mustTry = food.must_try || [];
  const toAvoid = food.dishes_to_avoid || [];
  const safeStarter = food.safe_starter;

  return (
    <section className="space-y-4">
      <header>
        <h3 className="font-display text-sm font-semibold text-forest">Sri Lankan flavours</h3>
        {food.narrative && (
          <p className="mt-1 text-xs leading-relaxed text-forest/60">{food.narrative}</p>
        )}
      </header>

      {mustTry.length > 0 && (
        <section>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-forest/50">
            Must try
          </h4>
          <section className="space-y-3">
            {mustTry.map((dish) => (
              <DishCard key={dishKey(dish)} dish={dish} />
            ))}
          </section>
        </section>
      )}

      {safeStarter && (
        <section>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gold-dark">
            Your safe starter
          </h4>
          <DishCard dish={safeStarter} highlighted />
        </section>
      )}

      {toAvoid.length > 0 && (
        <section>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-forest/50">
            Dishes to note
          </h4>
          <ul className="space-y-1 text-xs text-forest/65">
            {toAvoid.map((dish) => (
              <li key={typeof dish === "string" ? dish : dishKey(dish)} className="rounded-lg bg-cream-dark/50 px-3 py-2">
                {typeof dish === "string" ? dish : dishName(dish)}
              </li>
            ))}
          </ul>
        </section>
      )}
    </section>
  );
}

export default FoodGuideCard;
