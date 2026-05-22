"""Leafy Cave business rules for packages, attractions, food, and itineraries."""

import calendar
from datetime import datetime
from typing import Any

from models.attraction import Attraction
from models.food_item import FoodItem
from models.package import Package


class PackageRules:
    """Hard filters, scoring, and ranking for real Leafy Cave stay packages."""

    # Minimum score to treat a seeded package as a confident match (not custom-tailored).
    MIN_STRONG_MATCH_SCORE: float = 0.45

    CANONICAL_PACKAGE_NAMES: tuple[str, ...] = (
        "Love Nest Getaway",
        "Together Time Package",
        "Thrill & Chill Package",
        "Celebration Bliss Package",
        "Remote Work Retreat",
    )

    BUDGET_TIER_RANGES: dict[str, tuple[float, float]] = {
        "budget": (0, 50),
        "mid_range": (50, 150),
        "luxury": (150, 9999),
    }

    # Profile Builder travel_style values → package rule-base style tags.
    TRAVEL_STYLE_ALIASES: dict[str, list[str]] = {
        "relaxation": ["relaxation"],
        "adventure": ["adventure", "eco"],
        "nature": ["eco", "adventure", "relaxation"],
        "romance": ["romantic", "honeymoon", "relaxation"],
        "romantic": ["romantic", "honeymoon", "relaxation"],
        "wellness": ["relaxation", "eco"],
        "culture": ["cultural", "relaxation"],
        "cultural": ["cultural", "relaxation"],
        "luxury": ["luxury", "honeymoon", "romantic", "relaxation"],
        "budget": ["relaxation"],
        "family": ["family", "relaxation"],
        "eco": ["eco", "adventure"],
        "workation": ["workation", "eco", "relaxation"],
        "honeymoon": ["honeymoon", "romantic", "relaxation"],
    }

    GROUP_TYPE_LABELS: dict[str, str] = {
        "solo": "Solo",
        "couple": "Couple",
        "family": "Family",
        "group": "Group",
    }

    TRAVEL_STYLE_LABELS: dict[str, str] = {
        "relaxation": "Relaxation",
        "adventure": "Adventure",
        "nature": "Nature",
        "romance": "Romance",
        "wellness": "Wellness",
        "culture": "Culture",
        "luxury": "Luxury",
        "budget": "Budget-Friendly",
    }

    PACKAGE_GROUP_COMPATIBILITY: dict[str, list[str]] = {
        "Love Nest Getaway": ["couple"],
        "Together Time Package": ["family", "group"],
        "Thrill & Chill Package": ["couple", "family", "group"],
        "Celebration Bliss Package": ["family", "group", "couple"],
        "Remote Work Retreat": ["solo", "couple"],
    }

    PACKAGE_STYLE_MATCH: dict[str, list[str]] = {
        "Love Nest Getaway": ["honeymoon", "romantic", "relaxation"],
        "Together Time Package": ["family", "cultural", "relaxation"],
        "Thrill & Chill Package": ["adventure", "eco", "relaxation"],
        "Celebration Bliss Package": ["cultural", "relaxation", "family"],
        "Remote Work Retreat": ["relaxation", "eco", "workation"],
    }

    def filter_by_group_type(
        self, packages: list[Package], group_type: str
    ) -> list[Package]:
        """
        Hard filter — remove packages incompatible with guest group type.
        Example: Love Nest Getaway never shown to solo or family guests.
        """
        if not group_type:
            return list(packages)
        compatible = self.PACKAGE_GROUP_COMPATIBILITY
        gt = group_type.lower()
        return [
            p
            for p in packages
            if gt in compatible.get(p.name, [gt])
        ]

    def filter_by_special_occasion(
        self,
        packages: list[Package],
        special_occasions: str | None,
        profile: dict[str, Any] | None = None,
    ) -> list[Package]:
        """
        Boost occasion-matched packages to the top when keywords appear in
        special_occasions text or romance-style profile fields.
        """
        occ_text = (special_occasions or "").lower()
        travel_style = (profile or {}).get("travel_style")
        if isinstance(travel_style, list):
            occ_text = f"{occ_text} {' '.join(str(s) for s in travel_style)}"
        elif travel_style:
            occ_text = f"{occ_text} {travel_style}"
        if not occ_text.strip():
            return packages
        occ = occ_text.lower()

        work_triggers = [
            "work",
            "remote",
            "laptop",
            "digital nomad",
            "workation",
            "work from",
            "freelance",
            "office escape",
        ]
        romance_triggers = [
            "honeymoon",
            "anniversary",
            "romantic",
            "wedding",
            "proposal",
            "valentine",
        ]
        celebration_triggers = [
            "birthday",
            "party",
            "celebration",
            "bridal",
            "engagement",
            "get together",
            "reunion",
        ]

        def boost(pkgs: list[Package], name: str) -> list[Package]:
            target = [p for p in pkgs if p.name == name]
            rest = [p for p in pkgs if p.name != name]
            if target:
                setattr(target[0], "occasion_recommended", True)
            return target + rest

        result = list(packages)
        if any(t in occ for t in work_triggers):
            result = boost(result, "Remote Work Retreat")
        if any(t in occ for t in romance_triggers):
            result = boost(result, "Love Nest Getaway")
            if result and result[0].name == "Love Nest Getaway":
                setattr(result[0], "honeymoon_recommended", True)
        if any(t in occ for t in celebration_triggers):
            result = boost(result, "Celebration Bliss Package")
        return result

    def score_package(self, package: Package, profile: dict[str, Any]) -> float:
        """
        Score 0.0–1.0. Factors:
        - Group type hard match: 0.40 (non-negotiable)
        - Travel style overlap: 0.35
        - Duration match: 0.15
        - Special occasion boost: 0.10
        """
        score = 0.0
        group_type = (profile.get("group_type") or "").lower()
        compat = self.PACKAGE_GROUP_COMPATIBILITY.get(package.name, [])
        if group_type in compat:
            score += 0.40

        guest_styles = self._guest_travel_styles(profile)
        pkg_styles = set(self.PACKAGE_STYLE_MATCH.get(package.name, []))
        if guest_styles and pkg_styles:
            overlap = len(guest_styles & pkg_styles) / len(guest_styles)
            score += 0.35 * overlap

        guest_nights = int(profile.get("duration_nights") or 0)
        if package.min_nights and guest_nights >= package.min_nights:
            score += 0.15

        occ = (profile.get("special_occasions") or "").lower()
        work_triggers = ["work", "remote", "nomad", "workation", "freelance"]
        romance_triggers = ["honeymoon", "anniversary", "romantic", "wedding"]
        celebration_triggers = ["birthday", "bridal", "engagement", "party"]

        if "Remote Work" in package.name and any(t in occ for t in work_triggers):
            score += 0.10
        if "Love Nest" in package.name and any(t in occ for t in romance_triggers):
            score += 0.10
        if "Celebration" in package.name and any(
            t in occ for t in celebration_triggers
        ):
            score += 0.10

        return round(min(score, 1.0), 3)

    def is_strong_match(
        self, package: Package, profile: dict[str, Any], score: float
    ) -> bool:
        """True when group type fits and the rules engine score is high enough."""
        group_type = (profile.get("group_type") or "").lower()
        compat = self.PACKAGE_GROUP_COMPATIBILITY.get(package.name, [])
        if group_type and compat and group_type not in compat:
            return False
        return score >= self.MIN_STRONG_MATCH_SCORE

    def normalize_package_name(self, name: str) -> str | None:
        """Map LLM or fuzzy text to an exact seeded package name, if possible."""
        if not name or not str(name).strip():
            return None
        text = str(name).strip()
        for canonical in self.CANONICAL_PACKAGE_NAMES:
            if text.lower() == canonical.lower():
                return canonical
        lower = text.lower()
        for canonical in self.CANONICAL_PACKAGE_NAMES:
            if canonical.lower() in lower or lower in canonical.lower():
                return canonical
        return None

    def build_custom_package_name(self, profile: dict[str, Any]) -> str:
        """Generate a bespoke package title when no seeded package is a strong fit."""
        group = (profile.get("group_type") or "").lower()
        style = profile.get("travel_style")
        if isinstance(style, list):
            style_key = str(style[0]).lower() if style else ""
        else:
            style_key = str(style or "").lower()

        occ = (profile.get("special_occasions") or "").lower()
        celebration_triggers = [
            "birthday",
            "party",
            "celebration",
            "bridal",
            "engagement",
            "reunion",
            "anniversary",
        ]
        work_triggers = ["work", "remote", "nomad", "workation", "freelance", "digital nomad"]

        if any(t in occ for t in work_triggers) or style_key == "workation":
            return "Custom Remote Work Retreat at Leafy Cave"
        if any(t in occ for t in celebration_triggers):
            return "Custom Celebration Bliss Package at Leafy Cave"
        if style_key in ("romance", "romantic") or any(
            t in occ for t in ("honeymoon", "wedding", "proposal", "valentine")
        ):
            return "Custom Love Nest Getaway at Leafy Cave"

        group_label = self.GROUP_TYPE_LABELS.get(group, "Tailored")
        style_label = self.TRAVEL_STYLE_LABELS.get(
            style_key, style_key.replace("_", " ").title() if style_key else "Leafy Cave"
        )
        return f"Tailored {group_label} {style_label} Package at Leafy Cave"

    def get_scored_packages(
        self, packages: list[Package], profile: dict[str, Any]
    ) -> list[tuple[Package, float]]:
        """Return group-filtered packages with scores, highest first (occasion-boosted)."""
        filtered = self.filter_by_group_type(
            packages, profile.get("group_type", "")
        )
        if not filtered:
            return []

        scored = [
            (pkg, self.score_package(pkg, profile)) for pkg in filtered
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        boosted = self.filter_by_special_occasion(
            [pkg for pkg, _ in scored],
            profile.get("special_occasions"),
            profile=profile,
        )
        score_by_name = {pkg.name: score for pkg, score in scored}
        return [(pkg, score_by_name[pkg.name]) for pkg in boosted]

    def get_top_packages(
        self, packages: list[Package], profile: dict[str, Any], top_n: int = 2
    ) -> list[Package]:
        """
        Full pipeline:
        1. Hard filter by group type
        2. Score all remaining
        3. Apply special occasion boost
        4. Return up to top_n packages with strong match scores only
        """
        scored = self.get_scored_packages(packages, profile)
        strong = [
            pkg
            for pkg, score in scored
            if self.is_strong_match(pkg, profile, score)
        ]
        return strong[:top_n]

    @classmethod
    def _guest_travel_styles(cls, profile: dict[str, Any]) -> set[str]:
        styles: set[str] = set()
        travel_style = profile.get("travel_style")
        raw_styles: list[str] = []
        if travel_style:
            if isinstance(travel_style, list):
                raw_styles.extend(str(s).lower() for s in travel_style)
            else:
                raw_styles.append(str(travel_style).lower())
        for item in profile.get("interests") or []:
            raw_styles.append(str(item).lower())
        for raw in raw_styles:
            styles.update(cls.TRAVEL_STYLE_ALIASES.get(raw, [raw]))
        group = (profile.get("group_type") or "").lower()
        if group == "family":
            styles.add("family")
        if group == "group":
            styles.add("group")
        return styles

    @staticmethod
    def package_meta_text(package: Package) -> str:
        """Human-readable metadata for LLM context."""
        meta = package.package_meta or {}
        parts = []
        if meta.get("for_whom"):
            parts.append(f"Ideal for: {meta['for_whom']}")
        if meta.get("duration"):
            parts.append(f"Duration: {meta['duration']}")
        if meta.get("special_highlight"):
            parts.append(f"Highlight: {meta['special_highlight']}")
        if meta.get("customizations"):
            custom = meta["customizations"]
            if isinstance(custom, list):
                parts.append(f"Customizations: {', '.join(custom)}")
        return " | ".join(parts)


class AttractionRules:
    """Filtering and planning rules for verified Wellawaya-area attractions."""

    FITNESS_LEVEL_MAP: dict[str, list[str]] = {
        "low": ["Handapanagala Lake", "Alikota Ara Reservoir"],
        "moderate": [
            "Ella Wala Falls",
            "Diyaluma Waterfall",
            "Kalu Wala Falls",
        ],
        "high": [
            "Ravana Adventure Park (Pallewala Waterfall)",
            "Ella Rock & Ella Gap Viewpoint",
        ],
    }

    DISTANCE_BANDS: dict[str, tuple[float, float]] = {
        "easy": (0, 20),
        "moderate": (20, 40),
        "far": (40, 9999),
    }

    def filter_by_fitness(
        self, attractions: list[Attraction], fitness_level: str
    ) -> list[Attraction]:
        """
        Low fitness: only easy/low attractions (≤20km, low/moderate tag)
        Moderate fitness: exclude high-fitness only attractions
        High fitness: all attractions available
        """
        level_order = {"low": 0, "moderate": 1, "high": 2}
        guest_level = level_order.get((fitness_level or "moderate").lower(), 1)

        def attraction_level(att: Attraction) -> int:
            req = att.fitness_level_required
            value = req.value if hasattr(req, "value") else str(req)
            return level_order.get(value, 1)

        return [
            a for a in attractions if attraction_level(a) <= guest_level + 1
        ]

    def filter_by_duration(
        self, attractions: list[Attraction], duration_nights: int
    ) -> list[Attraction]:
        """
        1-night stay: only attractions ≤25km (can do in half day)
        2-night stay: all attractions available
        3+ nights: all attractions + can combine multiple per day
        """
        if duration_nights == 1:
            return [
                a
                for a in attractions
                if float(a.distance_km_from_cabana or 999) <= 25
            ]
        return list(attractions)

    def get_workation_attractions(
        self, attractions: list[Attraction]
    ) -> dict[str, list[Attraction]]:
        """
        For Remote Work Retreat guests:
        Prioritize low-effort, close, evening-friendly attractions.
        """
        easy = [
            a
            for a in attractions
            if float(a.distance_km_from_cabana or 999) <= 20
            and (
                a.fitness_level_required.value
                if hasattr(a.fitness_level_required, "value")
                else str(a.fitness_level_required)
            )
            in ("low", "moderate")
        ]
        optional_weekend = [
            a
            for a in attractions
            if (
                a.fitness_level_required.value
                if hasattr(a.fitness_level_required, "value")
                else str(a.fitness_level_required)
            )
            == "high"
        ]
        return {
            "weekday_recommended": easy,
            "weekend_optional": optional_weekend,
        }

    def max_activities_per_day(self, fitness_level: str) -> int:
        return {"low": 1, "moderate": 2, "high": 3}.get(
            (fitness_level or "moderate").lower(), 2
        )

    def flag_seasonal_warnings(
        self, attractions: list[Attraction], arrival_month: str
    ) -> list[str]:
        """
        Return warning strings for attractions with seasonal restrictions
        matching the guest's arrival month.
        """
        warnings: list[str] = []
        rain_months = ["May", "Jun", "Jul"]
        if arrival_month in rain_months:
            warnings.append(
                "Ella Rock & Ella Gap Viewpoint is not recommended "
                f"in {arrival_month} due to heavy cloud cover — "
                "the summit view is usually obscured. Consider "
                "Diyaluma Waterfall as an alternative."
            )
        return warnings

    def filter_seasonal(
        self, attractions: list[Attraction], arrival_date: str | None
    ) -> list[Attraction]:
        """Exclude attractions flagged in seasonal_availability.avoid for arrival month."""
        if not arrival_date:
            return list(attractions)

        try:
            arrival = datetime.fromisoformat(arrival_date.replace("Z", "+00:00"))
            month_name = calendar.month_name[arrival.month]
            month_abbr = calendar.month_abbr[arrival.month]
        except ValueError:
            return list(attractions)

        filtered: list[Attraction] = []
        for att in attractions:
            seasonal = att.seasonal_availability or {}
            avoid = seasonal.get("avoid") or []
            if not avoid:
                filtered.append(att)
                continue
            skip = any(
                token in (month_name, month_abbr, str(arrival.month))
                for token in avoid
                if token != "heavy_rain_days"
            )
            if not skip:
                filtered.append(att)

        return filtered if filtered else list(attractions)


class FoodRules:
    """Dietary filtering using real seeded Sri Lankan dish names."""

    DIETARY_EXCLUSIONS: dict[str, list[str]] = {
        "vegetarian": ["Fish Ambul Thiyal", "Kottu Roti"],
        "vegan": [
            "Fish Ambul Thiyal",
            "Kottu Roti",
            "Egg Hoppers",
            "Watalappan",
            "Pol Sambol",
        ],
        "halal": ["Kottu Roti"],
        "gluten_free": ["Kottu Roti", "Hoppers (Appam)", "Egg Hoppers"],
    }

    @classmethod
    def _normalize_restrictions(
        cls, dietary_restrictions: str | list[str] | None
    ) -> list[str]:
        if not dietary_restrictions:
            return []
        if isinstance(dietary_restrictions, list):
            raw = dietary_restrictions
        else:
            text = dietary_restrictions.lower().strip()
            if text in ("none", "no restrictions", "no restriction", "anything"):
                return []
            raw = [p.strip() for p in dietary_restrictions.replace(",", " ").split()]
        return [r.lower().replace(" ", "_") for r in raw if r]

    @classmethod
    def filter_by_dietary(
        cls,
        food_items: list[FoodItem],
        dietary_restrictions: str | list[str] | None,
    ) -> list[FoodItem]:
        restrictions = cls._normalize_restrictions(dietary_restrictions)
        if not restrictions or restrictions == ["none"]:
            return list(food_items)

        excluded: set[str] = set()
        for restriction in restrictions:
            key = restriction.replace("-", "_")
            if key in ("gluten", "gluten_free"):
                key = "gluten_free"
            excluded.update(cls.DIETARY_EXCLUSIONS.get(key, []))

        if not excluded:
            return list(food_items)
        return [f for f in food_items if f.name not in excluded]

    @classmethod
    def get_safe_starter(
        cls, food_items: list[FoodItem], dietary_restrictions: str | list[str] | None
    ) -> str:
        """
        For first-time Sri Lankan food guests, recommend the safest starter dish.
        """
        restrictions = cls._normalize_restrictions(dietary_restrictions)
        names = {f.name for f in food_items}
        if "vegan" in restrictions or "vegetarian" in restrictions:
            if "Dhal Curry (Parippu)" in names:
                return "Dhal Curry (Parippu)"
            return "Dhal Curry (Parippu)"
        if not restrictions:
            if "Egg Hoppers" in names:
                return "Egg Hoppers"
        if "Rice and Curry" in names:
            return "Rice and Curry"
        return food_items[0].name if food_items else "Rice and Curry"

    @staticmethod
    def flag_allergens(
        food_items: list[FoodItem],
        known_allergies: str | list[str] | None,
    ) -> list[str]:
        """Return dish names that contain allergens the guest must avoid."""
        if not known_allergies:
            return []

        if isinstance(known_allergies, str):
            allergy_tokens = [
                a.strip().lower()
                for a in known_allergies.replace(",", " ").split()
            ]
        else:
            allergy_tokens = [str(a).lower() for a in known_allergies]

        flagged: list[str] = []
        for item in food_items:
            allergens = [str(a).lower() for a in (item.allergens or [])]
            if any(
                token in allergens or any(token in a for a in allergens)
                for token in allergy_tokens
            ):
                flagged.append(item.name)
        return flagged


# Backward-compatible alias for itinerary planner import
class ItineraryRules:
    """Thin wrapper — delegates to AttractionRules for itinerary planning."""

    _attraction = AttractionRules()

    @classmethod
    def max_activities_per_day(cls, fitness_level: str | None) -> int:
        return cls._attraction.max_activities_per_day(fitness_level or "moderate")

    @staticmethod
    def filter_seasonal(
        attractions: list[Attraction],
        arrival_date: str | None,
    ) -> list[Attraction]:
        return AttractionRules().filter_seasonal(attractions, arrival_date)


def filter_packages_for_profile(
    packages: list[Package], preferences: dict[str, Any]
) -> list[Package]:
    """Apply package rules for a guest profile dict."""
    rules = PackageRules()
    profile = dict(preferences)

    active = [p for p in packages if p.is_active]
    size = int(profile.get("group_size") or 1)
    active = [p for p in active if p.max_guests >= size]

    nights = profile.get("duration_nights")
    if nights and int(nights) >= 1:
        active = [p for p in active if p.min_nights <= int(nights)]

    if not active:
        active = [p for p in packages if p.is_active]

    return rules.get_top_packages(active, profile, top_n=5)


def max_party_size_for_package(party_size: int) -> bool:
    """Whether party size fits Celebration Bliss (max 30 guests)."""
    return 1 <= party_size <= 30
