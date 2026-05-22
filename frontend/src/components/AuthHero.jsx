import { motion, useReducedMotion } from "framer-motion";
import LeafyCaveLogo from "./brand/LeafyCaveLogo.jsx";

function AuthHero() {
  const reduceMotion = useReducedMotion();

  return (
    <div className="relative flex flex-col justify-center overflow-hidden bg-premium-gradient px-10 py-16 text-cream lg:px-16">
      <div className="pointer-events-none absolute inset-0 bg-mesh-forest opacity-80" />
      {!reduceMotion && (
        <>
          <motion.div
            className="absolute -left-20 top-1/4 h-64 w-64 rounded-full bg-gold/20 blur-3xl"
            animate={{ x: [0, 30, 0], opacity: [0.3, 0.5, 0.3] }}
            transition={{ duration: 12, repeat: Infinity }}
          />
          <motion.div
            className="absolute -right-16 bottom-1/4 h-72 w-72 rounded-full bg-forest-light/30 blur-3xl"
            animate={{ x: [0, -25, 0] }}
            transition={{ duration: 16, repeat: Infinity, delay: 2 }}
          />
        </>
      )}

      <motion.div
        initial={reduceMotion ? false : { opacity: 0, x: -24 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-10"
      >
        <LeafyCaveLogo to="/" size="lg" className="[&_span]:text-cream" />

        <p className="mt-8 max-w-md text-lg font-light leading-relaxed text-cream/90 lg:text-xl">
          Your personal Sri Lanka experience, crafted by AI
        </p>

        <p className="mt-4 max-w-sm text-sm leading-relaxed text-cream/55">
          A luxury eco-retreat where warm hospitality meets intelligent travel planning —
          tailored for international guests at Leafy Cave, Wellawaya.
        </p>

        <ul className="mt-10 space-y-3 text-sm text-cream/70">
          {["Guided tap-through interviews", "Six specialist AI agents", "Curated cabana & island plans"].map(
            (item, i) => (
              <motion.li
                key={item}
                initial={reduceMotion ? false : { opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + i * 0.1 }}
                className="flex items-center gap-2"
              >
                <span className="h-1.5 w-1.5 rounded-full bg-gold" />
                {item}
              </motion.li>
            )
          )}
        </ul>
      </motion.div>
    </div>
  );
}

export default AuthHero;
