import { motion } from "framer-motion";

export default function GuidedStepper({ current = 1, total = 1, label }) {
  const pct = total > 0 ? Math.round((current / total) * 100) : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className="border-b border-cream-dark/80 bg-white/80 px-4 py-4 backdrop-blur-md lg:px-8"
    >
      <div className="mx-auto flex max-w-2xl items-center justify-between gap-4">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wider text-forest/45">
            {label || "Concierge interview"}
          </p>
          <p className="mt-0.5 font-display text-sm font-semibold text-forest">
            Question {current} of {total}
          </p>
        </div>
        <div className="flex w-36 flex-col items-end gap-1">
          <span className="text-xs font-medium text-gold-dark">{pct}%</span>
          <div className="h-2 w-full overflow-hidden rounded-full bg-cream-dark">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-gold via-gold-light to-forest"
              initial={{ width: 0 }}
              animate={{ width: `${pct}%` }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            />
          </div>
        </div>
      </div>
    </motion.div>
  );
}
