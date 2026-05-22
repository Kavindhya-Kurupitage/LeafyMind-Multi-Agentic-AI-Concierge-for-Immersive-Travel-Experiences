import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import LeafyCaveLogo from "../components/brand/LeafyCaveLogo.jsx";
import AppHeader from "../components/ui/AppHeader.jsx";
import PageBackdrop from "../components/ui/PageBackdrop.jsx";
import LoadingSpinner from "../components/LoadingSpinner.jsx";
import TripPackPanel from "../components/agents/TripPackPanel.jsx";
import { agentsAPI } from "../utils/api.js";
import { useAuth } from "../store/authStore.jsx";
import { cardHover, staggerContainer, transition } from "../utils/motion.js";

const HUB_AGENT_ORDER = [
  "profile_builder",
  "package_recommender",
  "food_guide",
  "itinerary_planner",
  "feedback_collector",
];

/** Dark, high-contrast card themes — do not use API `color` (often too light for cream text). */
const CARD_THEMES = {
  profile_builder: {
    gradient: "from-forest via-forest-light to-forest-dark",
    accent: "border-gold/50 shadow-gold",
    stepRing: "bg-gold text-forest",
  },
  package_recommender: {
    gradient: "from-forest-darker via-forest to-forest-light",
    accent: "border-cave-light/40",
    stepRing: "bg-cream/15 text-cream",
  },
  food_guide: {
    gradient: "from-forest-dark via-forest-muted to-forest",
    accent: "border-emerald-400/30",
    stepRing: "bg-cream/15 text-cream",
  },
  itinerary_planner: {
    gradient: "from-forest-darker via-forest-dark to-forest",
    accent: "border-sky-400/25",
    stepRing: "bg-cream/15 text-cream",
  },
  feedback_collector: {
    gradient: "from-forest-dark via-forest to-forest-light",
    accent: "border-gold/40",
    stepRing: "bg-cream/15 text-cream",
  },
};

const STEP_LABELS = {
  profile_builder: {
    step: 1,
    badge: "Required",
    hint: "8-step tap-through interview",
  },
  package_recommender: {
    step: 2,
    badge: "Optional",
    hint: "Priorities → package cards",
  },
  food_guide: {
    step: 3,
    badge: "Optional",
    hint: "Spice & meals → food guide",
  },
  itinerary_planner: {
    step: 4,
    badge: "Optional",
    hint: "Pace & themes → day plan",
  },
  feedback_collector: {
    step: 5,
    badge: "After planning",
    hint: "Star ratings + comment",
  },
};

const STATUS_STYLES = {
  locked: "bg-black/30 text-cream/50",
  available: "bg-cream/15 text-cream",
  in_progress: "bg-gold text-forest shadow-gold",
  completed: "bg-forest-light/80 text-cream border border-cream/20",
};

const STATUS_LABELS = {
  locked: "Locked",
  available: "Ready",
  in_progress: "In progress",
  completed: "Done",
};

function JourneyProgress({ journey }) {
  if (!journey) return null;
  const pct = journey.profile_completeness ?? 0;

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={transition}
      className="relative overflow-hidden rounded-2xl border border-forest/10 bg-gradient-to-br from-forest-darker via-forest to-forest-dark p-6 text-cream shadow-premium md:p-8"
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(201,168,76,0.15),transparent_60%)]" aria-hidden />
      <div className="relative flex flex-wrap items-start justify-between gap-6">
        <div className="flex min-w-0 flex-1 items-start gap-4">
          <LeafyCaveLogo to={null} size="sm" showWordmark={false} variant="light" />
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-gold/90">
              Your LeafyMind journey
            </p>
            <h2 className="mt-2 font-display text-2xl font-semibold md:text-3xl">
              {journey.profile_complete
                ? "Profile complete — choose a specialist"
                : "Start with your travel profile"}
            </h2>
            <p className="mt-2 max-w-xl text-sm leading-relaxed text-cream/75">
              {journey.trip_pack_ready
                ? "Your trip pack is ready — download or email your PDF below."
                : journey.profile_complete
                  ? "Finish Package, Food, and Itinerary to unlock your trip plan PDF."
                  : "Complete Profile Builder first — it unlocks Package, Food, and Itinerary."}
            </p>
          </div>
        </div>
        <div className="shrink-0 rounded-2xl border border-cream/15 bg-black/20 px-5 py-4 text-center backdrop-blur-sm">
          <p className="font-display text-4xl font-semibold text-gold">{pct}%</p>
          <p className="mt-1 text-[10px] font-medium uppercase tracking-wider text-cream/55">
            Profile complete
          </p>
        </div>
      </div>
      <div className="relative mt-6 h-2.5 overflow-hidden rounded-full bg-black/25">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-gold via-gold-light to-cream"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>
      {journey.trip_pack_ready && !journey.trip_pack_email_sent && (
        <p className="relative mt-5 rounded-xl border border-gold/35 bg-gold/15 px-4 py-3 text-sm text-cream">
          Scroll down to <strong>Download PDF</strong> or <strong>Email my plan</strong> — your full
          trip plan with food photos.
        </p>
      )}
      {journey.feedback_unlocked &&
        journey.trip_pack_ready &&
        !journey.feedback_survey_complete && (
        <p className="relative mt-5 rounded-xl border border-cream/20 bg-black/15 px-4 py-3 text-sm text-cream/85">
          {journey.feedback_email_sent
            ? "We also sent a short feedback survey link — optional, separate from your trip plan PDF."
            : "After you have your trip pack, Feedback Collector is available below."}
        </p>
      )}
    </motion.section>
  );
}

const MotionLink = motion.create(Link);
const MotionButton = motion.button;

function HubAgentCard({ agent, stepInfo, stepState, onLockedClick }) {
  const locked = stepState?.locked ?? false;
  const status = stepState?.status ?? "available";
  const threadId = stepState?.thread_id;
  const to = threadId ? `/agents/${agent.id}/threads/${threadId}` : `/agents/${agent.id}`;
  const theme = CARD_THEMES[agent.id] || CARD_THEMES.profile_builder;
  const isRequired = agent.id === "profile_builder";
  const highlight =
    agent.id === "feedback_collector" && status === "available" && !locked;

  const cardClasses = [
    "hub-agent-card group relative flex h-full min-h-[320px] w-full flex-col overflow-hidden rounded-2xl border p-5 text-left no-underline text-cream shadow-luxury transition-all duration-300",
    `bg-gradient-to-br ${theme.gradient}`,
    theme.accent,
    locked ? "cursor-not-allowed opacity-70" : "hover:-translate-y-1 hover:shadow-premium",
    highlight ? "ring-2 ring-gold ring-offset-2 ring-offset-cream" : "",
    status === "in_progress" && !locked ? "ring-2 ring-gold/60 ring-offset-2 ring-offset-cream" : "",
  ].join(" ");

  const content = (
    <>
      <div
        className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-gold/10 blur-2xl"
        aria-hidden
      />
      <div className="relative flex items-start justify-between gap-2">
        <span
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-sm font-bold ${theme.stepRing}`}
        >
          {stepInfo.step}
        </span>
        <span
          className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide ${
            isRequired ? "bg-gold/25 text-gold" : "bg-cream/10 text-cream/85"
          }`}
        >
          {stepInfo.badge}
        </span>
      </div>

      <div className="relative mt-5 flex h-14 w-14 items-center justify-center rounded-2xl border border-cream/15 bg-black/20 text-3xl shadow-inner backdrop-blur-sm">
        {agent.icon}
      </div>

      <h3 className="relative mt-4 font-display text-xl font-semibold leading-tight text-cream">
        {agent.name}
      </h3>
      <p className="relative mt-1 text-sm font-medium text-gold/90">{agent.tagline}</p>
      <p className="relative mt-2 text-xs text-cream/70">{stepInfo.hint}</p>
      <p className="relative mt-2 min-h-[4.25rem] flex-1 text-sm leading-relaxed text-cream/80 line-clamp-3">
        {agent.description}
      </p>

      <div className="relative mt-auto flex items-center justify-between gap-2 border-t border-cream/10 pt-4">
        <span
          className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide ${
            STATUS_STYLES[status] || STATUS_STYLES.available
          }`}
        >
          {STATUS_LABELS[status] || status}
        </span>
        {!locked ? (
          <span className="text-sm font-semibold text-gold transition group-hover:translate-x-0.5">
            {status === "completed" ? "View again →" : "Open →"}
          </span>
        ) : (
          <span className="text-xs text-cream/45">Complete prior steps</span>
        )}
      </div>
    </>
  );

  if (locked) {
    return (
      <MotionButton
        type="button"
        className={`${cardClasses} w-full`}
        onClick={() => onLockedClick(agent.id)}
        aria-disabled="true"
        variants={cardHover}
        initial="rest"
        whileHover="hover"
        whileTap="tap"
      >
        <div className="absolute inset-0 z-10 rounded-2xl bg-forest-darker/50 backdrop-blur-[1px]" />
        <div className="relative z-0 flex h-full w-full flex-col">{content}</div>
      </MotionButton>
    );
  }

  return (
    <MotionLink
      to={to}
      className={`${cardClasses} w-full`}
      variants={cardHover}
      initial="rest"
      whileHover="hover"
      whileTap="tap"
    >
      {content}
    </MotionLink>
  );
}

function AgentHubPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [agents, setAgents] = useState([]);
  const [journey, setJourney] = useState(null);
  const [lockMessage, setLockMessage] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadHub = useCallback(async () => {
    const agentList = await agentsAPI.listAgents();
    setAgents(agentList);
    try {
      const journeyData = await agentsAPI.getJourney();
      setJourney(journeyData);
      return journeyData;
    } catch (journeyErr) {
      console.warn("Journey status unavailable:", journeyErr);
      setJourney(null);
      return null;
    }
  }, []);

  useEffect(() => {
    loadHub()
      .catch((err) => setError(err.message || "Could not load dashboard"))
      .finally(() => setIsLoading(false));
  }, [loadHub]);

  useEffect(() => {
    const openFeedback = searchParams.get("feedback") === "1";
    if (!journey || !openFeedback) return;
    if (journey.feedback_unlocked && !journey.feedback_survey_complete) {
      navigate("/agents/feedback_collector", { replace: true });
    } else {
      setSearchParams({}, { replace: true });
    }
  }, [journey, navigate, searchParams, setSearchParams]);

  const handleLogout = async () => {
    await logout();
    navigate("/signin", { replace: true });
  };

  const handleLockedClick = (agentId) => {
    if (agentId === "feedback_collector") {
      setLockMessage(
        "Finish your profile, then use a planning agent. Feedback unlocks after that."
      );
    } else {
      setLockMessage("Complete Profile Builder first — it unlocks all other specialists.");
    }
  };

  const hubAgents = HUB_AGENT_ORDER.map((id) => agents.find((a) => a.id === id)).filter(Boolean);

  if (isLoading) {
    return <LoadingSpinner message="Loading your dashboard…" />;
  }

  return (
    <div className="relative min-h-screen bg-cream">
      <PageBackdrop />
      <AppHeader
        title="Your LeafyMind Dashboard"
        subtitle="Five AI specialists · one guided journey"
        user={user}
        onLogout={handleLogout}
        homeTo="/"
      />

      <motion.main
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="relative mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:py-10"
      >
        {error && (
          <div className="auth-error mb-8" role="alert">
            {error}
          </div>
        )}

        {lockMessage && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-gold/40 bg-gold/15 px-4 py-3 text-sm text-forest"
            role="status"
          >
            <span>{lockMessage}</span>
            <button type="button" className="font-semibold underline" onClick={() => setLockMessage(null)}>
              Dismiss
            </button>
          </motion.div>
        )}

        <JourneyProgress journey={journey} />

        <TripPackPanel
          journey={journey}
          onEmailSent={() => loadHub().catch(() => {})}
        />

        <section className="mt-12">
          <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
            <div>
              <h2 className="font-display text-2xl font-semibold text-forest md:text-3xl">
                Your AI specialists
              </h2>
              <p className="mt-2 max-w-lg text-sm text-forest/60">
                Tap a card to start a guided interview. Optional agents unlock after your profile is
                complete.
              </p>
            </div>
            <p className="text-xs font-medium uppercase tracking-wider text-forest/40">
              1 required · 3 optional · feedback last
            </p>
          </div>

          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="hub-cards-grid"
          >
            {hubAgents.map((agent, i) => (
              <motion.div
                key={agent.id}
                className="hub-card-cell"
                variants={{
                  hidden: { opacity: 0, y: 24 },
                  visible: { opacity: 1, y: 0, transition: { delay: i * 0.07 } },
                }}
              >
                <HubAgentCard
                  agent={agent}
                  stepInfo={STEP_LABELS[agent.id]}
                  stepState={journey?.steps?.[agent.id]}
                  onLockedClick={handleLockedClick}
                />
              </motion.div>
            ))}
          </motion.div>
        </section>

        <p className="mt-14 text-center text-sm text-forest/45">
          Prefer one continuous chat?{" "}
          <Link to="/chat" className="font-medium text-forest underline decoration-gold/50 hover:text-gold-dark">
            Open full concierge
          </Link>
        </p>
      </motion.main>
    </div>
  );
}

export default AgentHubPage;
