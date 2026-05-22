import { Link } from "react-router-dom";
import { motion, useReducedMotion } from "framer-motion";
import LandingNav from "../components/landing/LandingNav.jsx";
import ScrollReveal from "../components/landing/ScrollReveal.jsx";
import AnimatedChatPreview from "../components/landing/AnimatedChatPreview.jsx";
import { useAuth } from "../store/authStore.jsx";
import {
  fadeUp,
  fadeIn,
  floatOrb,
  staggerContainer,
  transition,
  viewport,
} from "../utils/motion.js";

const AGENTS = [
  {
    name: "Orchestrator",
    role: "Your concierge conductor",
    description:
      "Routes every message through the right specialist — never overlapping, always coherent.",
    icon: "✦",
    color: "from-gold/20 to-gold/5 border-gold/25",
  },
  {
    name: "Profile Builder",
    role: "Knows your travel DNA",
    description:
      "Learns budget, dietary needs, pace, and interests through natural conversation.",
    icon: "◎",
    color: "from-forest-light/20 to-forest/5 border-forest-light/30",
  },
  {
    name: "Package Recommender",
    role: "Cabana & stay curator",
    description:
      "Matches you to Leafy Cave packages with transparent pricing and inclusions.",
    icon: "🏡",
    color: "from-cave-light/25 to-cave/5 border-cave/30",
  },
  {
    name: "Food Guide",
    role: "Sri Lankan cuisine expert",
    description:
      "Vegetarian, halal, allergies — every meal suggestion respects your table.",
    icon: "🍃",
    color: "from-emerald-500/15 to-emerald-700/5 border-emerald-600/25",
  },
  {
    name: "Itinerary Planner",
    role: "Day-by-day architect",
    description:
      "Waterfalls, temples, hikes — balanced days that breathe with the island rhythm.",
    icon: "🗺",
    color: "from-sky-500/15 to-sky-700/5 border-sky-600/25",
  },
  {
    name: "Feedback Collector",
    role: "Continuous refinement",
    description:
      "Captures what delighted you so every future stay feels even more personal.",
    icon: "✺",
    color: "from-rose-400/15 to-rose-600/5 border-rose-400/25",
  },
];

const JOURNEY = [
  {
    phase: "01",
    title: "Profiling",
    body: "Share who you are travelling with, your budget, and what moves you — no forms, just chat.",
  },
  {
    phase: "02",
    title: "Recommending",
    body: "Receive curated cabana packages and dining guidance tailored to your profile.",
  },
  {
    phase: "03",
    title: "Itinerary",
    body: "Approve a day-by-day plan with local experiences, transport notes, and timing.",
  },
  {
    phase: "04",
    title: "Feedback",
    body: "Refine and book — your preferences shape every future recommendation.",
  },
];

const STATS = [
  { value: "6", label: "AI specialists" },
  { value: "24/7", label: "Concierge access" },
  { value: "100%", label: "Sri Lanka curated" },
];

const TRUST = [
  "Leafy Cave boutique cabana",
  "Multi-agent orchestration",
  "Streaming live responses",
  "Owner insights dashboard",
];

const FEATURES = [
  {
    icon: "💬",
    title: "Streaming concierge",
    body: "Token-by-token replies with phase indicators so you always know what the AI is doing.",
  },
  {
    icon: "📋",
    title: "Live recommendation panels",
    body: "Packages, food guides, and itineraries appear beside the chat as they are composed.",
  },
  {
    icon: "🔒",
    title: "Secure by design",
    body: "JWT sessions, role-based access, and sanitized prompts protect guest data.",
  },
  {
    icon: "📊",
    title: "Owner analytics",
    body: "Feedback trends and session insights help Leafy Cave refine the guest experience.",
  },
];

function HeroOrbs({ reduceMotion }) {
  if (reduceMotion) return null;

  return (
    <>
      <motion.div
        className="pointer-events-none absolute -left-24 top-1/4 h-72 w-72 rounded-full bg-gold/20 blur-3xl"
        aria-hidden="true"
        animate={floatOrb(0)}
      />
      <motion.div
        className="pointer-events-none absolute -right-16 bottom-1/4 h-64 w-64 rounded-full bg-forest-light/30 blur-3xl"
        aria-hidden="true"
        animate={floatOrb(1.2)}
      />
      <motion.div
        className="pointer-events-none absolute left-1/2 top-12 h-40 w-40 -translate-x-1/2 rounded-full bg-cream/10 blur-2xl"
        aria-hidden="true"
        animate={floatOrb(0.6)}
      />
    </>
  );
}

function LandingPage() {
  const { isAuthenticated } = useAuth();
  const reduceMotion = useReducedMotion();

  return (
    <div className="min-h-screen bg-cream text-forest">
      <LandingNav />

      {/* Hero */}
      <section className="relative min-h-[92vh] overflow-hidden bg-forest-darker">
        <motion.div
          className="absolute inset-0"
          initial={reduceMotion ? false : { scale: 1.08 }}
          animate={{ scale: 1.12 }}
          transition={{ duration: 22, ease: "easeOut" }}
        >
          <img
            src="/images/hero-cabana.png"
            alt="Leafy Cave luxury cabana at dusk"
            className="absolute inset-0 h-full w-full object-cover"
          />
          <motion.div className="absolute inset-0 bg-gradient-to-r from-forest-darker/75 via-forest-darker/40 to-forest-darker/20" />
          <motion.div className="absolute inset-0 bg-gradient-to-t from-forest-darker via-transparent to-transparent" />
        </motion.div>

        <HeroOrbs reduceMotion={reduceMotion} />

        <motion.div
          className="relative mx-auto flex min-h-[92vh] max-w-7xl flex-col justify-end px-4 pb-20 pt-32 lg:px-8 lg:pb-28"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          <motion.p
            variants={fadeUp}
            transition={transition}
            className="mb-4 inline-flex w-fit items-center gap-2 rounded-full border border-gold/30 bg-forest-darker/60 px-4 py-1.5 text-xs uppercase tracking-[0.25em] text-gold backdrop-blur-sm"
          >
            <motion.span
              className="h-1.5 w-1.5 rounded-full bg-gold"
              animate={reduceMotion ? {} : { scale: [1, 1.4, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            />
            Leafy Cave · Sri Lanka
          </motion.p>

          <motion.h1
            variants={fadeUp}
            transition={transition}
            className="max-w-3xl font-display text-4xl font-semibold leading-tight text-cream sm:text-5xl lg:text-6xl"
          >
            Your AI concierge for{" "}
            <span className="text-gradient-gold">unforgettable</span> island escapes
          </motion.h1>

          <motion.p
            variants={fadeUp}
            transition={transition}
            className="mt-6 max-w-xl text-lg text-cream/80"
          >
            Six specialist agents work in concert — profiling, recommending packages,
            guiding cuisine, and crafting itineraries for Leafy Cave guests.
          </motion.p>

          <motion.div
            variants={fadeUp}
            transition={transition}
            className="btn-row-group mt-10"
          >
            {isAuthenticated ? (
              <motion.div whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.98 }} className="w-full sm:w-auto">
                <Link to="/hub" className="btn-gold btn-row w-full sm:w-auto">
                  Open concierge
                </Link>
              </motion.div>
            ) : (
              <>
                <motion.div whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.98 }} className="w-full sm:w-auto">
                  <Link to="/register" className="btn-gold btn-row w-full sm:w-auto">
                    Start planning
                  </Link>
                </motion.div>
                <motion.div whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.98 }} className="w-full sm:w-auto">
                  <Link to="/signin" className="btn-outline-light btn-row w-full sm:w-auto">
                    Sign in
                  </Link>
                </motion.div>
              </>
            )}
            <motion.a
              href="#preview"
              className="btn-outline-light btn-row w-full sm:w-auto"
              whileHover={{ scale: 1.04, borderColor: "rgba(201,168,76,0.6)" }}
              whileTap={{ scale: 0.98 }}
            >
              See it in action
            </motion.a>
          </motion.div>

          <motion.ul
            variants={staggerContainer}
            className="mt-14 grid gap-6 border-t border-cream/10 pt-10 sm:grid-cols-3"
          >
            {STATS.map((s) => (
              <motion.li key={s.label} variants={fadeUp} transition={transition}>
                <p className="font-display text-3xl font-semibold text-gold">{s.value}</p>
                <p className="mt-1 text-sm text-cream/60">{s.label}</p>
              </motion.li>
            ))}
          </motion.ul>
        </motion.div>

        <motion.div
          className="absolute bottom-8 left-1/2 -translate-x-1/2 text-cream/40"
          aria-hidden="true"
          animate={reduceMotion ? {} : { y: [0, 8, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        >
          <span className="block h-8 w-5 rounded-full border border-cream/30" />
        </motion.div>
      </section>

      {/* Trust strip */}
      <motion.section
        className="border-b border-cream-dark bg-white py-5"
        initial="hidden"
        whileInView="visible"
        viewport={viewport}
        variants={staggerContainer}
      >
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-center gap-x-10 gap-y-3 px-4 lg:px-8">
          {TRUST.map((item) => (
            <motion.span
              key={item}
              variants={fadeIn}
              transition={transition}
              className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-forest/55"
            >
              <span className="text-gold">✦</span>
              {item}
            </motion.span>
          ))}
        </div>
      </motion.section>

      {/* Agents */}
      <section id="agents" className="py-24 lg:py-32">
        <div className="mx-auto max-w-7xl px-4 lg:px-8">
          <ScrollReveal className="mx-auto max-w-2xl text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-gold-dark">
              Multi-agent system
            </p>
            <h2 className="mt-4 font-display text-3xl font-semibold text-forest sm:text-4xl">
              Six minds, one seamless conversation
            </h2>
            <p className="mt-4 text-forest/65">
              Each specialist owns a domain. The orchestrator ensures you never juggle
              multiple threads — just one elegant dialogue.
            </p>
          </ScrollReveal>

          <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {AGENTS.map((agent, i) => (
              <ScrollReveal key={agent.name} delay={i * 80} direction="scale">
                <motion.article
                  className={`group agent-card h-full border bg-gradient-to-br ${agent.color}`}
                  whileHover={reduceMotion ? {} : { y: -10, scale: 1.02 }}
                  transition={{ type: "spring", stiffness: 320, damping: 22 }}
                >
                  <motion.span
                    className="agent-icon inline-flex text-3xl"
                    whileHover={reduceMotion ? {} : { scale: 1.15, rotate: 6 }}
                  >
                    {agent.icon}
                  </motion.span>
                  <h3 className="mt-4 font-display text-xl font-semibold">{agent.name}</h3>
                  <p className="mt-1 text-xs font-medium uppercase tracking-wider text-gold-dark">
                    {agent.role}
                  </p>
                  <p className="mt-3 text-sm leading-relaxed text-forest/70">
                    {agent.description}
                  </p>
                </motion.article>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* Journey */}
      <section
        id="journey"
        className="relative overflow-hidden bg-forest-darker py-24 text-cream lg:py-32"
      >
        <div
          className="pointer-events-none absolute inset-0 opacity-30"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 50%, rgba(201,168,76,0.15), transparent 50%), radial-gradient(circle at 80% 20%, rgba(45,106,79,0.2), transparent 40%)",
          }}
          aria-hidden="true"
        />

        <div className="relative mx-auto max-w-7xl px-4 lg:px-8">
          <ScrollReveal className="mx-auto max-w-2xl text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-gold/80">
              Your journey
            </p>
            <h2 className="mt-4 font-display text-3xl font-semibold sm:text-4xl">
              From first message to perfect stay
            </h2>
          </ScrollReveal>

          <div className="relative mt-16">
            <motion.div
              className="journey-line origin-left"
              aria-hidden="true"
              initial={{ scaleX: 0 }}
              whileInView={{ scaleX: 1 }}
              viewport={viewport}
              transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
            />
            <ol className="grid gap-10 lg:grid-cols-4">
              {JOURNEY.map((step, i) => (
                <ScrollReveal key={step.phase} delay={i * 100} as="li">
                  <motion.div
                    className="relative text-center lg:text-left"
                    whileHover={reduceMotion ? {} : { x: 4 }}
                    transition={{ type: "spring", stiffness: 400, damping: 25 }}
                  >
                    <motion.span
                      className="inline-flex h-16 w-16 items-center justify-center rounded-2xl border border-gold/30 bg-gold/10 font-display text-lg text-gold"
                      whileHover={reduceMotion ? {} : { scale: 1.08, boxShadow: "0 0 24px rgba(201,168,76,0.25)" }}
                    >
                      {step.phase}
                    </motion.span>
                    <h3 className="mt-5 font-display text-xl font-semibold">{step.title}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-cream/70">{step.body}</p>
                  </motion.div>
                </ScrollReveal>
              ))}
            </ol>
          </div>
        </div>
      </section>

      {/* Experiences */}
      <section className="py-24 lg:py-32">
        <motion.div className="mx-auto max-w-7xl px-4 lg:px-8">
          <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
            <ScrollReveal direction="left">
              <motion.div
                className="overflow-hidden rounded-3xl shadow-luxury"
                whileHover={reduceMotion ? {} : { scale: 1.02 }}
                transition={{ type: "spring", stiffness: 300, damping: 24 }}
              >
                <motion.img
                  src="/images/experiences.png"
                  alt="Sri Lankan temple and waterfall experiences"
                  className="h-full w-full object-cover"
                  whileHover={reduceMotion ? {} : { scale: 1.06 }}
                  transition={{ duration: 0.6 }}
                />
              </motion.div>
            </ScrollReveal>
            <ScrollReveal direction="right" delay={100}>
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-gold-dark">
                Experiences
              </p>
              <h2 className="mt-4 font-display text-3xl font-semibold">
                Curated beyond the guidebook
              </h2>
              <p className="mt-4 leading-relaxed text-forest/70">
                Your itinerary planner balances adventure with rest — dawn temple visits,
                hidden waterfalls, and village encounters paced for how you actually travel.
              </p>
              <ul className="mt-6 space-y-3 text-sm text-forest/80">
                {[
                  "Real-time adjustments in chat",
                  "Local expert tone, not generic lists",
                  "Synced with your cabana package",
                ].map((item, i) => (
                  <motion.li
                    key={item}
                    className="flex items-start gap-2"
                    initial={reduceMotion ? false : { opacity: 0, x: -12 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={viewport}
                    transition={{ ...transition, delay: 0.15 + i * 0.08 }}
                  >
                    <span className="mt-0.5 text-gold">✦</span>
                    {item}
                  </motion.li>
                ))}
              </ul>
            </ScrollReveal>
          </div>
        </motion.div>
      </section>

      {/* Cuisine */}
      <section className="bg-cream-light py-24 lg:py-32">
        <motion.div className="mx-auto max-w-7xl px-4 lg:px-8">
          <motion.div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
            <ScrollReveal direction="left" delay={80} className="order-2 lg:order-1">
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-gold-dark">
                Cuisine
              </p>
              <h2 className="mt-4 font-display text-3xl font-semibold">
                Every plate respects your table
              </h2>
              <p className="mt-4 leading-relaxed text-forest/70">
                The food guide knows Sri Lankan flavours and your dietary boundaries —
                vegetarian thalis, halal options, and allergy-safe recommendations at Leafy Cave
                and beyond.
              </p>
            </ScrollReveal>
            <ScrollReveal direction="right" className="order-1 lg:order-2">
              <motion.div
                className="overflow-hidden rounded-3xl shadow-luxury"
                whileHover={reduceMotion ? {} : { scale: 1.02 }}
                transition={{ type: "spring", stiffness: 300, damping: 24 }}
              >
                <motion.img
                  src="/images/cuisine.png"
                  alt="Sri Lankan cuisine spread"
                  className="h-full w-full object-cover"
                  whileHover={reduceMotion ? {} : { scale: 1.06 }}
                  transition={{ duration: 0.6 }}
                />
              </motion.div>
            </ScrollReveal>
          </motion.div>
        </motion.div>
      </section>

      {/* Chat preview */}
      <section id="preview" className="py-24 lg:py-32">
        <div className="mx-auto max-w-7xl px-4 lg:px-8">
          <ScrollReveal className="mx-auto max-w-2xl text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-gold-dark">
              Live preview
            </p>
            <h2 className="mt-4 font-display text-3xl font-semibold sm:text-4xl">
              Watch the concierge think in real time
            </h2>
            <p className="mt-4 text-forest/65">
              Phases cycle as agents hand off — profiling, recommending, and building your plan.
            </p>
          </ScrollReveal>

          <ScrollReveal delay={150} className="mt-12">
            <AnimatedChatPreview />
          </ScrollReveal>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="border-t border-cream-dark bg-white py-24 lg:py-32">
        <div className="mx-auto max-w-7xl px-4 lg:px-8">
          <ScrollReveal className="mx-auto max-w-2xl text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-gold-dark">
              Platform
            </p>
            <h2 className="mt-4 font-display text-3xl font-semibold sm:text-4xl">
              Built for guests and owners alike
            </h2>
          </ScrollReveal>

          <div className="mt-16 grid gap-6 sm:grid-cols-2">
            {FEATURES.map((f, i) => (
              <ScrollReveal key={f.title} delay={i * 70}>
                <motion.article
                  className="feature-card h-full"
                  whileHover={reduceMotion ? {} : { y: -6, borderColor: "rgba(201,168,76,0.35)" }}
                  transition={{ type: "spring", stiffness: 350, damping: 22 }}
                >
                  <motion.span
                    className="inline-block text-2xl"
                    whileHover={reduceMotion ? {} : { scale: 1.2, rotate: -8 }}
                  >
                    {f.icon}
                  </motion.span>
                  <h3 className="mt-4 font-display text-xl font-semibold">{f.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-forest/70">{f.body}</p>
                </motion.article>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative overflow-hidden bg-forest py-20 text-cream">
        <motion.div
          className="pointer-events-none absolute inset-0 opacity-40"
          style={{
            background:
              "linear-gradient(120deg, transparent, rgba(201,168,76,0.2), transparent)",
            backgroundSize: "200% 200%",
          }}
          aria-hidden="true"
          animate={reduceMotion ? {} : { backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"] }}
          transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
        />
        <ScrollReveal className="relative mx-auto max-w-3xl px-4 text-center lg:px-8">
          <h2 className="font-display text-3xl font-semibold sm:text-4xl">
            Ready to plan your Leafy Cave escape?
          </h2>
          <p className="mt-4 text-cream/75">
            Create a free account and let LeafyMind orchestrate your perfect Sri Lankan stay.
          </p>
          <motion.div
            className="btn-row-group-center mt-10"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={viewport}
          >
            <motion.div variants={fadeUp} transition={transition} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.98 }}>
              <Link
                to={isAuthenticated ? "/hub" : "/register"}
                className="btn-gold btn-row !min-w-[12rem]"
              >
                {isAuthenticated ? "Continue in concierge" : "Get started free"}
              </Link>
            </motion.div>
            <motion.a
              href="#agents"
              variants={fadeUp}
              transition={transition}
              className="btn-outline-light btn-row !min-w-[12rem]"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.98 }}
            >
              Meet the agents
            </motion.a>
          </motion.div>
        </ScrollReveal>
      </section>

      <motion.footer
        className="border-t border-forest-dark bg-forest-darker py-10 text-center text-sm text-cream/50"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={viewport}
        transition={transition}
      >
        <p>© {new Date().getFullYear()} Leafy Cave · LeafyMind AI Concierge</p>
      </motion.footer>
    </div>
  );
}

export default LandingPage;
