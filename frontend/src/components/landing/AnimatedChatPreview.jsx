import { useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { fadeIn, slideLeft, transition } from "../../utils/motion.js";

const DEMO_STEPS = [
  {
    phase: "Profile",
    question: "Who is travelling with you?",
    options: ["Solo", "Couple", "Family", "Group"],
    selection: "Couple",
    reply: "Mid-range comfort, vegetarian, 5 nights — hiking & waterfalls.",
  },
  {
    phase: "Packages",
    question: "What matters most in your stay?",
    options: ["Privacy", "Views", "Meals", "Excursions"],
    selection: "Views, Meals",
    reply: "Nature Immersion fits beautifully — deluxe cabana, all meals included…",
  },
  {
    phase: "Itinerary",
    question: "What pace feels right?",
    options: ["Relaxed", "Balanced", "Packed"],
    selection: "Balanced",
    reply: "Day 2: sunrise safari, afternoon Ella waterfalls — paced for your group.",
  },
];

function AnimatedChatPreview() {
  const [stepIdx, setStepIdx] = useState(0);
  const [showResult, setShowResult] = useState(false);
  const reduceMotion = useReducedMotion();
  const step = DEMO_STEPS[stepIdx];

  useEffect(() => {
    const phaseTimer = setInterval(() => {
      setStepIdx((i) => (i + 1) % DEMO_STEPS.length);
      setShowResult(false);
      setTimeout(() => setShowResult(true), 1400);
    }, 5500);
    const initial = setTimeout(() => setShowResult(true), 1000);
    return () => {
      clearInterval(phaseTimer);
      clearTimeout(initial);
    };
  }, []);

  return (
    <motion.section
      className="overflow-hidden rounded-3xl border border-cream-dark bg-white shadow-luxury landing-shine"
      initial={reduceMotion ? false : { opacity: 0, y: 32 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ ...transition, duration: 0.8 }}
    >
      <header className="flex items-center gap-2 border-b border-cream-dark bg-forest px-6 py-4">
        <motion.span
          className="h-3 w-3 rounded-full bg-red-400/80"
          animate={reduceMotion ? {} : { scale: [1, 1.2, 1], opacity: [0.7, 1, 0.7] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        />
        <span className="h-3 w-3 rounded-full bg-gold/80" />
        <span className="h-3 w-3 rounded-full bg-forest-light/80" />
        <span className="ml-4 text-sm text-cream/70">LeafyMind Agent Hub</span>
        <motion.span
          className="ml-auto rounded-full bg-gold/20 px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-gold"
          animate={reduceMotion ? {} : { opacity: [0.6, 1, 0.6] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          Guided
        </motion.span>
      </header>
      <motion.div className="grid lg:grid-cols-5">
        <aside className="hidden border-r border-cream-dark bg-forest p-6 lg:col-span-1 lg:block">
          <p className="text-xs uppercase tracking-wider text-gold/70">Your journey</p>
          <p className="mt-4 text-sm text-cream/80">Profile → Plan → Feedback</p>
          <p className="mt-2 text-sm text-cream/50">Tap options, optional text</p>
        </aside>
        <div className="bg-cream p-6 lg:col-span-3">
          <AnimatePresence mode="wait">
            <motion.p
              key={stepIdx}
              className="mb-4 text-center text-[10px] uppercase tracking-wider text-forest/45"
              variants={fadeIn}
              initial="hidden"
              animate="visible"
              exit="hidden"
              transition={{ duration: 0.35 }}
            >
              ✦ {step.phase} specialist ✦
            </motion.p>
          </AnimatePresence>
          <div className="space-y-4">
            <motion.div
              className="max-w-[92%] rounded-2xl rounded-tl-md border border-forest/15 bg-white px-4 py-4 text-sm text-forest shadow-sm"
              variants={slideLeft}
              initial="hidden"
              animate="visible"
              transition={{ ...transition, delay: 0.15 }}
            >
              <span className="mb-2 inline-block rounded-full bg-forest px-2 py-0.5 text-[9px] font-semibold uppercase text-cream">
                {step.phase}
              </span>
              <p className="font-medium">{step.question}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {step.options.map((opt) => (
                  <span
                    key={opt}
                    className={`rounded-lg border px-2.5 py-1.5 text-xs ${
                      step.selection.includes(opt)
                        ? "border-forest bg-forest text-cream"
                        : "border-forest/15 bg-cream text-forest/70"
                    }`}
                  >
                    {opt}
                  </span>
                ))}
              </div>
            </motion.div>
            <motion.div
              className="ml-auto max-w-[75%] rounded-2xl rounded-tr-md bg-gold px-4 py-2.5 text-xs font-medium text-forest shadow-gold"
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 }}
            >
              Selected: {step.selection}
            </motion.div>
            <AnimatePresence mode="wait">
              {showResult ? (
                <motion.div
                  key="reply"
                  className="max-w-[88%] rounded-2xl rounded-tl-md border border-gold/25 bg-white px-4 py-3 text-sm text-forest shadow-sm"
                  variants={slideLeft}
                  initial="hidden"
                  animate="visible"
                  exit="hidden"
                  transition={transition}
                >
                  <p className="leading-relaxed">{step.reply}</p>
                </motion.div>
              ) : (
                <motion.div
                  key="typing"
                  className="flex max-w-[50%] gap-1.5 rounded-2xl border border-forest/10 bg-white px-4 py-3"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  {[0, 150, 300].map((d) => (
                    <motion.span
                      key={d}
                      className="h-2 w-2 rounded-full bg-forest/30"
                      animate={reduceMotion ? {} : { y: [0, -5, 0] }}
                      transition={{ duration: 1.2, repeat: Infinity, delay: d / 1000 }}
                    />
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
        <aside className="hidden border-l border-cream-dark bg-cream-light p-6 lg:col-span-1 lg:block">
          <p className="text-xs font-semibold uppercase text-forest/45">Your plan</p>
          <AnimatePresence>
            {showResult && (
              <motion.div
                className="mt-4 rounded-xl border border-gold/30 bg-white p-3"
                initial={{ opacity: 0, y: 12, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8 }}
                transition={transition}
              >
                <p className="text-xs font-semibold text-forest">Personalised output</p>
                <p className="text-[10px] text-gold-dark">Built from your taps</p>
              </motion.div>
            )}
          </AnimatePresence>
        </aside>
      </motion.div>
    </motion.section>
  );
}

export default AnimatedChatPreview;
