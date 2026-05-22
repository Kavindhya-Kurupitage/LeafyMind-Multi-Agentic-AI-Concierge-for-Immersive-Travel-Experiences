"""Generate branded Leafy Cave trip plan PDFs from aggregated trip summary data."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import settings
from services.food_image_service import food_image_service

logger = logging.getLogger(__name__)

FOREST = (26, 71, 49)
GOLD = (201, 168, 76)
CREAM = (245, 240, 232)
MUTED = (90, 107, 95)


class TripPdfService:
    """Build a styled PDF with profile, packages, food photos, and itinerary."""

    def __init__(self) -> None:
        self._public_dir = Path(settings.public_assets_dir)

    def _logo_path(self) -> Path | None:
        for name in ("logo.png", "logo.jpg", "logo.jpeg", "logo.webp"):
            path = self._public_dir / name
            if path.is_file():
                return path
        return None

    def _dish_image_path(self, dish: dict[str, Any]) -> Path | None:
        image = dish.get("image") or {}
        url = image.get("url") or ""
        if "/images/food/" in url:
            filename = url.split("/images/food/")[-1].split("?")[0]
            path = Path(settings.food_images_dir) / filename
            if path.is_file():
                return path
        local = food_image_service.resolve_local(dish.get("dish_name") or dish.get("name") or "")
        if local and local.get("url"):
            filename = local["url"].split("/images/food/")[-1].split("?")[0]
            path = Path(settings.food_images_dir) / filename
            if path.is_file():
                return path
        return None

    def _prepare_sections(self, summary: dict[str, Any]) -> dict[str, Any]:
        profile = summary.get("profile") or {}
        dietary = profile.get("dietary_restrictions")
        if isinstance(dietary, list):
            dietary_str = ", ".join(str(d) for d in dietary) if dietary else "None"
        else:
            dietary_str = str(dietary or "None")

        packages = []
        for pkg in (summary.get("packages") or {}).get("recommendations") or []:
            if not isinstance(pkg, dict):
                continue
            why = pkg.get("why_this_fits") or pkg.get("fit_reason") or ""
            why = re.sub(r"\*+", "", why)[:400]
            packages.append(
                {
                    "name": pkg.get("package_name") or pkg.get("name") or "Package",
                    "price": pkg.get("price_per_night_usd") or pkg.get("price"),
                    "min_nights": pkg.get("min_nights"),
                    "why": why,
                    "inclusions": (pkg.get("inclusions") or pkg.get("includes") or [])[:6],
                }
            )

        food = summary.get("food") or {}
        dishes = []
        for dish in food.get("must_try") or []:
            if isinstance(dish, str):
                dish = {"dish_name": dish}
            if not isinstance(dish, dict):
                continue
            name = dish.get("dish_name") or dish.get("name") or "Dish"
            desc = dish.get("description_plain_english") or dish.get("description") or ""
            dishes.append(
                {
                    "name": name,
                    "spice": dish.get("spice_level") or dish.get("spice"),
                    "description": desc[:260],
                    "image_path": self._dish_image_path(dish),
                }
            )

        safe = food.get("safe_starter")
        safe_name = None
        if isinstance(safe, dict):
            safe_name = safe.get("dish_name") or safe.get("name")

        itinerary = summary.get("itinerary") or {}
        days = []
        for day in itinerary.get("itinerary") or []:
            if not isinstance(day, dict):
                continue
            activities = []
            for act in day.get("activities") or []:
                if isinstance(act, dict):
                    activities.append(
                        {
                            "slot": act.get("time_slot") or act.get("period") or "Activity",
                            "name": act.get("attraction_name") or act.get("name") or "",
                            "description": (act.get("description") or "")[:180],
                        }
                    )
            days.append(
                {
                    "day_number": day.get("day") or day.get("day_number") or len(days) + 1,
                    "theme": day.get("theme") or "",
                    "activities": activities,
                }
            )

        return {
            "guest_name": summary.get("guest_name") or "Guest",
            "profile": profile,
            "dietary": dietary_str,
            "packages": packages,
            "packages_narrative": ((summary.get("packages") or {}).get("narrative") or "")[:500],
            "food_narrative": (food.get("narrative") or "")[:500],
            "dishes": dishes,
            "safe_starter": safe_name,
            "days": days,
            "itinerary_narrative": (itinerary.get("narrative") or "")[:500],
            "generated_at": datetime.now(timezone.utc).strftime("%d %B %Y"),
        }

    def generate_pdf(self, summary: dict[str, Any]) -> bytes:
        try:
            from fpdf import FPDF
        except ImportError as exc:
            raise RuntimeError("PDF generation is not available on this server") from exc

        ctx = self._prepare_sections(summary)
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=18)
        pdf.set_margins(18, 18, 18)
        pdf.add_page()

        self._draw_header(pdf, self._logo_path())
        self._section_title(pdf, "Your travel profile")
        self._draw_profile(pdf, ctx)
        self._section_title(pdf, "Recommended cabana packages")
        if ctx["packages_narrative"]:
            self._body_text(pdf, ctx["packages_narrative"], italic=True)
        for pkg in ctx["packages"]:
            self._draw_package(pdf, pkg)
        self._section_title(pdf, "Sri Lankan food guide")
        if ctx["food_narrative"]:
            self._body_text(pdf, ctx["food_narrative"], italic=True)
        if ctx["safe_starter"]:
            self._body_text(pdf, f"Safe starter: {ctx['safe_starter']}", bold=True)
        for dish in ctx["dishes"]:
            self._draw_dish(pdf, dish)
        self._section_title(pdf, "Day-by-day itinerary")
        if ctx["itinerary_narrative"]:
            self._body_text(pdf, ctx["itinerary_narrative"], italic=True)
        for day in ctx["days"]:
            self._draw_day(pdf, day)
        self._draw_footer(pdf, ctx["generated_at"])

        out = pdf.output()
        if isinstance(out, (bytes, bytearray)):
            return bytes(out)
        return out.encode("latin-1", errors="replace")

    @staticmethod
    def _draw_header(pdf: Any, logo: Path | None) -> None:
        pdf.set_fill_color(*FOREST)
        pdf.rect(0, 0, 210, 42, style="F")
        if logo:
            try:
                pdf.image(str(logo), x=75, y=8, w=60)
            except Exception:
                pdf.set_xy(18, 14)
                pdf.set_font("Helvetica", "B", 22)
                pdf.set_text_color(*GOLD)
                pdf.cell(0, 10, "LEAFY CAVE", align="C")
        else:
            pdf.set_xy(18, 14)
            pdf.set_font("Helvetica", "B", 22)
            pdf.set_text_color(*GOLD)
            pdf.cell(0, 10, "LEAFY CAVE", align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*CREAM)
        pdf.set_xy(18, 28)
        pdf.cell(0, 6, "Luxury Cabana - Wellawaya, Sri Lanka", align="C")
        pdf.set_xy(18, 34)
        pdf.cell(0, 5, "Personalised trip plan by LeafyMind", align="C")
        pdf.set_y(48)
        pdf.set_text_color(*FOREST)

    @staticmethod
    def _section_title(pdf: Any, title: str) -> None:
        if pdf.get_y() > 250:
            pdf.add_page()
        pdf.ln(4)
        pdf.set_fill_color(*GOLD)
        pdf.set_text_color(*FOREST)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    @staticmethod
    def _body_text(pdf: Any, text: str, *, italic: bool = False, bold: bool = False) -> None:
        style = ""
        if bold:
            style = "B"
        elif italic:
            style = "I"
        pdf.set_font("Helvetica", style, 10)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(0, 5, text)
        pdf.ln(2)
        pdf.set_text_color(*FOREST)

    def _draw_profile(self, pdf: Any, ctx: dict[str, Any]) -> None:
        profile = ctx["profile"]
        rows = [
            ("Guest", ctx["guest_name"]),
            ("Group", f"{profile.get('group_type') or '-'} ({profile.get('group_size') or '-'} guests)"),
            ("Travel style", str(profile.get("travel_style") or "-")),
            ("Stay", f"{profile.get('duration_nights') or '-'} nights"),
            ("Budget", str(profile.get("budget_tier") or "-")),
            ("Dietary", ctx["dietary"]),
        ]
        if profile.get("special_occasions"):
            rows.append(("Occasion", str(profile["special_occasions"])))
        for label, value in rows:
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*MUTED)
            pdf.cell(0, 5, label.upper(), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*FOREST)
            pdf.multi_cell(0, 5, str(value))
            pdf.ln(1)

    @staticmethod
    def _draw_package(pdf: Any, pkg: dict[str, Any]) -> None:
        if pdf.get_y() > 240:
            pdf.add_page()
        pdf.set_fill_color(*CREAM)
        y = pdf.get_y()
        pdf.rect(18, y, 174, 8, style="F")
        pdf.set_xy(20, y + 1)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*FOREST)
        pdf.cell(0, 6, pkg["name"])
        pdf.ln(7)
        if pkg.get("price"):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*GOLD)
            nights = f" - min {pkg['min_nights']} nights" if pkg.get("min_nights") else ""
            pdf.cell(0, 5, f"USD {pkg['price']} / night{nights}")
            pdf.ln(5)
        if pkg.get("why"):
            TripPdfService._body_text(pdf, pkg["why"])
        if pkg.get("inclusions"):
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*FOREST)
            pdf.cell(0, 5, "Includes:")
            pdf.ln(4)
            pdf.set_font("Helvetica", "", 9)
            for item in pkg["inclusions"]:
                pdf.cell(0, 4, f"  - {item}")
                pdf.ln(4)
        pdf.ln(3)

    @staticmethod
    def _draw_dish(pdf: Any, dish: dict[str, Any]) -> None:
        if pdf.get_y() > 220:
            pdf.add_page()
        y = pdf.get_y()
        img_path = dish.get("image_path")
        text_x = 20
        if img_path and Path(img_path).is_file():
            try:
                pdf.image(str(img_path), x=20, y=y, w=42, h=32)
                text_x = 66
            except Exception:
                pass
        pdf.set_xy(text_x, y)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*FOREST)
        pdf.cell(0, 6, dish["name"])
        pdf.ln(5)
        if dish.get("spice"):
            pdf.set_x(text_x)
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(*MUTED)
            pdf.cell(0, 4, f"Spice: {dish['spice']}")
            pdf.ln(4)
        if dish.get("description"):
            pdf.set_x(text_x)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*FOREST)
            pdf.multi_cell(120 if text_x > 30 else 0, 4, dish["description"])
        pdf.set_y(max(pdf.get_y(), y + 36))
        pdf.ln(4)

    @staticmethod
    def _draw_day(pdf: Any, day: dict[str, Any]) -> None:
        if pdf.get_y() > 245:
            pdf.add_page()
        title = f"Day {day['day_number']}"
        if day.get("theme"):
            title += f" - {day['theme']}"
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*FOREST)
        pdf.cell(0, 6, title)
        pdf.ln(6)
        for act in day.get("activities") or []:
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*GOLD)
            pdf.cell(0, 4, str(act.get("slot", "")))
            pdf.ln(4)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*FOREST)
            line = act.get("name", "")
            if act.get("description"):
                line += f" - {act['description']}"
            pdf.multi_cell(0, 4, line)
            pdf.ln(2)
        pdf.ln(2)

    @staticmethod
    def _draw_footer(pdf: Any, generated_at: str) -> None:
        pdf.ln(6)
        pdf.set_draw_color(*GOLD)
        pdf.line(18, pdf.get_y(), 192, pdf.get_y())
        pdf.ln(4)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 4, "Leafy Cave Luxury Cabana - Wellawaya, Sri Lanka", align="C")
        pdf.ln(4)
        pdf.cell(0, 4, f"Generated {generated_at} - LeafyMind AI Concierge", align="C")


trip_pdf_service = TripPdfService()
