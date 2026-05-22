import { motion, useReducedMotion } from "framer-motion";

/**
 * Ambient mesh orbs for premium page backgrounds.
 */
export default function PageBackdrop({ variant = "cream" }) {
  const reduceMotion = useReducedMotion();
  if (reduceMotion) return null;

  const isDark = variant === "forest";

  return (
    <div className="pointer-events-none fixed inset-0 overflow-hidden" aria-hidden>
      <motion.div
        className={`absolute -left-32 top-20 h-96 w-96 rounded-full blur-3xl ${
          isDark ? "bg-gold/15" : "bg-gold/25"
        }`}
        animate={{ x: [0, 40, 0], y: [0, -30, 0] }}
        transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className={`absolute -right-24 bottom-32 h-80 w-80 rounded-full blur-3xl ${
          isDark ? "bg-forest-light/25" : "bg-forest-light/20"
        }`}
        animate={{ x: [0, -35, 0], y: [0, 25, 0] }}
        transition={{ duration: 22, repeat: Infinity, ease: "easeInOut", delay: 1 }}
      />
      <motion.div
        className={`absolute left-1/2 top-1/3 h-64 w-64 -translate-x-1/2 rounded-full blur-3xl ${
          isDark ? "bg-cream/5" : "bg-forest/8"
        }`}
        animate={{ scale: [1, 1.08, 1], opacity: [0.4, 0.7, 0.4] }}
        transition={{ duration: 14, repeat: Infinity, ease: "easeInOut" }}
      />
    </div>
  );
}
