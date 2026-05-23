"""Generate docs/LOOM_DEMO_SCRIPT.pdf for the 5-minute Loom video demo."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs" / "LOOM_DEMO_SCRIPT.pdf"

FOREST = (26, 71, 49)
GOLD = (201, 168, 76)
MUTED = (90, 107, 95)


def _ascii(text: str) -> str:
    """fpdf2 Helvetica is Latin-1 only; normalize common Unicode punctuation."""
    return (
        text.replace("\u2014", " - ")
        .replace("\u2013", "-")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2026", "...")
        .replace("\u2192", "->")
        .replace("\u2193", "v")
    )


class LoomScriptPDF(FPDF):
    def _t(self, text: str) -> str:
        return _ascii(text)

    def cell(self, w, h=0, text="", *args, **kwargs):  # type: ignore[no-untyped-def]
        return super().cell(w, h, self._t(str(text)), *args, **kwargs)

    def multi_cell(self, w, h=0, text="", *args, **kwargs):  # type: ignore[no-untyped-def]
        return super().multi_cell(w, h, self._t(str(text)), *args, **kwargs)
    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 8, "LeafyMind - 5-Minute Loom Demo Script", align="R", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def title_block(self, title: str, subtitle: str) -> None:
        self.set_fill_color(*FOREST)
        self.rect(0, 0, 210, 42, style="F")
        self.set_y(12)
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, title, align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 11)
        self.set_text_color(*GOLD)
        self.cell(0, 8, subtitle, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(14)
        self.set_text_color(0, 0, 0)

    def h1(self, text: str) -> None:
        self.ln(4)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*FOREST)
        self.multi_cell(0, 8, text)
        self.set_draw_color(*GOLD)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)
        self.set_text_color(0, 0, 0)

    def h2(self, text: str) -> None:
        self.ln(2)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*FOREST)
        self.multi_cell(0, 7, text)
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def body(self, text: str) -> None:
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, text: str) -> None:
        self.set_font("Helvetica", "", 10)
        x = self.get_x()
        self.cell(6, 5.5, "-")
        self.set_x(x + 6)
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def quote_block(self, text: str) -> None:
        self.set_fill_color(245, 240, 232)
        self.set_font("Helvetica", "I", 10)
        y = self.get_y()
        self.set_x(14)
        self.multi_cell(182, 5.5, text, fill=True)
        self.ln(3)
        self.set_font("Helvetica", "", 10)

    def table_row(self, cols: list[str], bold: bool = False) -> None:
        w = [28, 32, 130]
        style = "B" if bold else ""
        self.set_font("Helvetica", style, 9)
        for i, (txt, width) in enumerate(zip(cols, w)):
            self.cell(width, 7, txt[:80], border=1, new_x="RIGHT", new_y="TOP")
        self.ln(7)

    def code_block(self, text: str) -> None:
        self.set_font("Courier", "", 8)
        self.set_fill_color(240, 240, 240)
        for line in _ascii(text.strip()).split("\n"):
            if self.get_y() > 270:
                self.add_page()
            self.cell(0, 5, "  " + line, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)
        self.set_font("Helvetica", "", 10)


def build_pdf() -> Path:
    pdf = LoomScriptPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.title_block(
        "LeafyMind",
        "5-Minute Loom Demo Script - Multi-Agent AI Concierge for Leafy Cave",
    )

    pdf.h1("Overview")
    pdf.body(
        "Suggested video title: LeafyMind - AI Concierge for Leafy Cave "
        "(Multi-Agent + Rules + RAG). Target length: 4:45-5:15. "
        "Before recording: docker compose up, seed data, Groq API key in .env, "
        "fresh guest account, http://localhost:5174/hub ready."
    )

    pdf.h2("Pre-recording checklist")
    pdf.bullet("docker compose up - all services healthy")
    pdf.bullet("Seed packages, attractions, food (see README Quick start)")
    pdf.bullet("New guest email ready (profile not yet complete)")
    pdf.bullet("Food images in frontend/public/images/food/")
    pdf.bullet("Terminal tab: docker compose ps + optional test command")
    pdf.bullet("Browser zoom 100%, hide bookmarks bar")

    pdf.h1("Minute-by-minute flow")
    pdf.table_row(["Time", "Section", "On screen"], bold=True)
    pdf.table_row(["0:00-0:35", "Hook + problem", "Landing or /hub"])
    pdf.table_row(["0:35-1:10", "Architecture + stack", "README diagram / docker ps"])
    pdf.table_row(["1:10-2:00", "Register + Profile", "Agent Hub -> Profile Builder"])
    pdf.table_row(["2:00-3:15", "Three planners", "Package -> Food -> Itinerary"])
    pdf.table_row(["3:15-4:15", "Trip pack + tech", "Trip pack PDF + terminal"])
    pdf.table_row(["4:15-5:00", "Evals + close", "test script + /owner mention"])

    pdf.add_page()
    pdf.h1("Section 1 - Hook (0:00-0:35)")
    pdf.quote_block(
        'Hi, I am [Your name]. This is LeafyMind - an AI-native pre-arrival concierge '
        "I built for Leafy Cave, a luxury cabana retreat in Wellawaya, Sri Lanka.\n\n"
        "The real problem: international guests ask the same questions over and over on "
        "WhatsApp - which cabana package fits a couple versus a family, what to eat with "
        "dietary limits, how to plan days around Ella and waterfalls, and local culture "
        "like spice levels. The owner had no single shareable plan before guests fly.\n\n"
        "LeafyMind fixes that with a guided multi-agent hub, business rules so packages "
        "do not hallucinate, and a branded trip-plan PDF guests can download or email."
    )
    pdf.body("ACTION: Show landing page -> click Agent Hub (/hub).")

    pdf.h1("Section 2 - Architecture & technologies (0:35-1:10)")
    pdf.quote_block(
        "Under the hood this is a full production-style stack, not a ChatGPT wrapper.\n\n"
        "Frontend: React 18, Vite, Tailwind - guest UI at /hub, /chat, and /owner.\n"
        "BFF: Node Express - CORS, Helmet, rate limits, proxies /api; browser never sees API keys.\n"
        "Backend: Python FastAPI, async SQLAlchemy, PostgreSQL 15.\n"
        "AI layer: LangChain specialists on Groq through a single LLM gateway.\n\n"
        "Multi-agent design - five Hub specialists plus classic orchestrator concierge on /chat. "
        "Agents do not call each other; orchestrator and agent runner route work.\n"
        "Business rules engine - package matching in business_rules.py with scores and guards.\n"
        "RAG / semantic retrieval - FAISS indexes over packages, food, attractions; "
        "sentence-transformers embeddings.\n"
        "Structured artifacts - JSON per agent (profile, packages, food, itinerary) for UI cards and PDF.\n"
        "External grounding - OpenTripMap, Unsplash, Gmail SMTP.\n"
        "Everything runs in Docker Compose."
    )
    pdf.body("ACTION: Flash README architecture or docker compose ps for 5 seconds.")

    pdf.h1("Section 3 - Profile Builder (1:10-2:00)")
    pdf.quote_block(
        "I register as a new guest - JWT auth, bcrypt passwords, role guest.\n\n"
        "Step one is Profile Builder - an eight-step guided interview (tap-through). "
        "The LLM extracts preferences; the flow is structured: group type, travel style, "
        "budget, dietary needs, nights, and contact.\n\n"
        "This profile is the source of truth. Package, food, and itinerary stay locked "
        "until profile completes.\n\n"
        "Notice SSE streaming - Server-Sent Events over POST - so replies feel live."
    )
    pdf.body("ACTION: Register -> complete Profile Builder -> show planners unlock.")

    pdf.add_page()
    pdf.h1("Section 4 - Package Planner (2:00-2:40)")
    pdf.quote_block(
        "Package Planner is where rules beat creativity. The system scores canonical packages "
        "like Love Nest Getaway and Together Time Package against the profile. "
        "There is a minimum strong-match score; below that we generate a custom package name.\n\n"
        "Group-type guards stop obvious mistakes - romance packages do not surface for families. "
        "The LLM writes the warm narrative; the package list is rule-grounded."
    )
    pdf.body("ACTION: Open Package Planner -> show recommendations card / artifact sidebar.")

    pdf.h1("Section 5 - Food Guide (2:40-3:05)")
    pdf.quote_block(
        "Food Guide combines semantic KB retrieval with structured output: must-try dishes, "
        "spice level, safe starters. Photos from local food library with Unsplash fallback. "
        "Guests see FoodGuideCard, not broken markdown in chat.\n\n"
        "We fixed a real bug: artifacts over chat markdown for anything the UI must render."
    )
    pdf.body("ACTION: Show food cards with photos and spice labels.")

    pdf.h1("Section 6 - Itinerary Planner (3:05-3:15)")
    pdf.quote_block(
        "Itinerary Planner blends curated PostgreSQL attractions with OpenTripMap discoveries "
        "near cabana coordinates. Structured day-by-day JSON feeds timeline UI and PDF.\n\n"
        "When all three planners finish, the hub marks trip pack ready."
    )
    pdf.body("ACTION: Show itinerary timeline (2–3 days is enough).")

    pdf.h1("Section 7 - Trip pack (3:15-4:00)")
    pdf.quote_block(
        "This is the MVP outcome: Your trip pack. One branded PDF — profile, packages, "
        "food with photos, itinerary - generated with fpdf2, not ask the LLM to make a PDF.\n\n"
        "Guests download immediately or email my plan if SMTP is configured. "
        "Feedback survey email only fires after all three planners - separate triggers.\n\n"
        "Workflow: Profile -> three specialists -> trip summary service -> PDF/email -> "
        "feedback -> owner dashboard on /owner."
    )
    pdf.body("ACTION: Download PDF -> scroll profile, food photo, itinerary. Mention email button.")

    pdf.add_page()
    pdf.h1("Section 8 - Classic chat & evaluation (4:00-4:35)")
    pdf.quote_block(
        "Classic streaming concierge on /chat - multi-phase orchestrator: profiling, contact, "
        "recommending, itinerary, feedback. Same backend rules and KB, different UX.\n\n"
        "We ship automated checks: Agent Hub flow script, package rule unit tests, auth smoke, "
        "verify external services. Package recommendations are regression-testable."
    )
    pdf.body("ACTION (optional): Flash /chat for 10 seconds.")
    pdf.code_block(
        "docker exec leafymind-backend python -m scripts.test_agent_hub_flow"
    )

    pdf.h1("Section 9 - Close (4:35-5:00)")
    pdf.quote_block(
        "Security: secrets server-side, BFF rate limits, prompt sanitisation, JWT on API routes.\n\n"
        "Built in a five-day forward-deploy trial using Cursor with project rules - "
        "no LLM calls from frontend, no agents calling agents, versioned SQL migrations.\n\n"
        "LeafyMind turns repetitive owner WhatsApp work into a self-serve, rule-grounded, "
        "multi-agent journey with a document guests can pack. Repo and setup in README. Thanks for watching."
    )
    pdf.body("ACTION: End on /hub with trip pack visible or PDF cover.")

    pdf.h1("Tech stack diagram")
    pdf.code_block(
        """Guest → React (Vite) → Express BFF → FastAPI → PostgreSQL
                          ↓
        LangChain multi-agents (Groq) + orchestrator
                          ↓
     Rules engine | FAISS RAG (MiniLM) | Artifacts JSON
                          ↓
        OpenTripMap | Unsplash | Gmail SMTP → Trip PDF"""
    )

    pdf.h1("Bullet cheat sheet (pin next to monitor)")
    for item in [
        "Problem - WhatsApp overload, no shareable plan",
        "Stack - React -> BFF -> FastAPI -> Postgres, Docker",
        "Multi-agent - 5 hub agents + orchestrator; runner coordinates",
        "Rules - business_rules.py, scores, custom packages",
        "RAG - FAISS + sentence-transformers on packages/food/attractions",
        "Artifacts - JSON per agent -> UI cards + PDF",
        "SSE - streaming hub messages",
        "Integrations - OpenTripMap, Unsplash, Gmail",
        "Trip pack - fpdf2 PDF after 3 planners",
        "Tests - test_agent_hub_flow, package rules pytest",
        "Security - JWT, BFF limits, secrets server-side",
        "AI dev - Cursor rules, docs, eval scripts",
    ]:
        pdf.bullet(item)

    pdf.h1("Loom video description (paste under upload)")
    pdf.code_block(
        """LeafyMind - AI concierge for Leafy Cave (Wellawaya, Sri Lanka).

Tech: React + Express BFF + FastAPI + PostgreSQL | LangChain multi-agents (Groq)
| Business rules engine | FAISS RAG (sentence-transformers) | SSE streaming
| OpenTripMap + Unsplash + Gmail | Branded trip PDF (fpdf2)

Demo path: /hub -> Profile -> Package / Food / Itinerary -> Trip pack PDF

Repo: [your GitHub URL]
Live: [your URL if deployed]"""
    )

    pdf.h1("Recording tips")
    pdf.bullet("Do not read every guided step - tap quickly and narrate structure.")
    pdf.bullet("Pause 2 seconds on food photos and PDF scroll - visual proof beats jargon.")
    pdf.bullet('Say "rules before LLM creativity" once — key differentiator.')
    pdf.bullet("Run one test command in terminal - evaluators love it.")
    pdf.bullet("If live demo breaks: cut to a PDF you already downloaded.")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    path = build_pdf()
    print(f"Wrote {path}")
