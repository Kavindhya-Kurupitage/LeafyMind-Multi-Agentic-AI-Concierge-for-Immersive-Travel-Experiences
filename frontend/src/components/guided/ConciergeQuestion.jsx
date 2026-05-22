import { motion } from "framer-motion";
import AgentBadge from "../chat/AgentBadge.jsx";

export default function ConciergeQuestion({ agentName, agentIcon, turn }) {
  if (!turn) return null;
  const intro = turn.intro || "";
  const question = turn.question || "";

  return (
    <motion.article
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="mx-auto max-w-2xl"
    >
      <header className="mb-4 flex items-center gap-3">
        {agentIcon && (
          <motion.span
            className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-gold/25 to-forest/10 text-2xl shadow-gold"
            animate={{ rotate: [0, 3, -3, 0] }}
            transition={{ duration: 6, repeat: Infinity }}
          >
            {agentIcon}
          </motion.span>
        )}
        {agentName && <AgentBadge agent={agentName} />}
      </header>
      <div className="premium-panel relative overflow-hidden p-6 shadow-premium">
        <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-gold via-forest-light to-gold" />
        {intro && <p className="text-sm leading-relaxed text-forest/65">{intro}</p>}
        <p className="mt-4 whitespace-pre-wrap font-display text-xl font-semibold leading-snug text-forest md:text-2xl">
          {question}
        </p>
      </div>
    </motion.article>
  );
}
