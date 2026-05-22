import { motion } from "framer-motion";

function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex max-w-[60%] gap-2 rounded-2xl border border-forest/10 bg-white/90 px-5 py-4 shadow-glass backdrop-blur-sm"
      role="status"
      aria-label="Assistant is typing"
    >
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="h-2.5 w-2.5 rounded-full bg-gradient-to-br from-gold to-forest"
          animate={{ y: [0, -6, 0], opacity: [0.35, 1, 0.35] }}
          transition={{ duration: 1.1, repeat: Infinity, delay: i * 0.15 }}
        />
      ))}
    </motion.div>
  );
}

export default TypingIndicator;
