import { motion, AnimatePresence } from "framer-motion";

function ToolActivityFeed({ activities }) {
  if (!activities?.length) return null;

  return (
    <section className="relative z-10 border-b border-cream-dark/60 bg-white/70 px-4 py-3 backdrop-blur-md">
      <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-forest/45">
        Agent activity
      </p>
      <ul className="space-y-2">
        <AnimatePresence>
          {activities.map((item) => (
            <motion.li
              key={item.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-2 text-xs text-forest/70"
            >
              <span
                className={`h-2 w-2 shrink-0 rounded-full ${
                  item.status === "running"
                    ? "animate-pulse bg-gold shadow-gold"
                    : "bg-forest-light"
                }`}
              />
              <span>{item.label || item.tool}</span>
            </motion.li>
          ))}
        </AnimatePresence>
      </ul>
    </section>
  );
}

export default ToolActivityFeed;
