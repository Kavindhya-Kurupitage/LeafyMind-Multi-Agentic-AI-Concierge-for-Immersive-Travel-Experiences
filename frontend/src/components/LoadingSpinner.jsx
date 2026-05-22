import { motion } from "framer-motion";
import LeafyCaveLogo from "./brand/LeafyCaveLogo.jsx";
import PageBackdrop from "./ui/PageBackdrop.jsx";

function LoadingSpinner({ message = "Preparing your experience…" }) {
  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-premium-gradient text-cream">
      <PageBackdrop variant="forest" />
      <motion.div
        initial={{ opacity: 0, scale: 0.92 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-10 text-center"
      >
        <div className="mx-auto mb-8 flex flex-col items-center gap-4">
          <div className="animate-logo-pulse rounded-full">
            <LeafyCaveLogo size="hero" to={null} showWordmark={false} animate={false} />
          </div>
          <p className="font-display text-xl font-semibold text-cream">Leafy Cave</p>
        </div>
        <p className="text-sm text-cream/70">{message}</p>
        <div className="mx-auto mt-8 flex gap-2" role="status" aria-label="Loading">
          {[0, 1, 2].map((i) => (
            <motion.span
              key={i}
              className="h-2 w-2 rounded-full bg-gold"
              animate={{ y: [0, -8, 0], opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.15 }}
            />
          ))}
        </div>
      </motion.div>
    </div>
  );
}

export default LoadingSpinner;
