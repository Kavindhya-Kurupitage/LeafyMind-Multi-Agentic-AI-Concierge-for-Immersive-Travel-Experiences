import { motion } from "framer-motion";

/**
 * Premium glass surface with subtle hover lift.
 */
export default function GlassCard({
  children,
  className = "",
  hover = true,
  delay = 0,
  as: Component = motion.div,
}) {
  const props = {
    initial: { opacity: 0, y: 16 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] },
    className: `glass-card ${hover ? "glass-card-hover" : ""} ${className}`,
  };
  return <Component {...props}>{children}</Component>;
}
