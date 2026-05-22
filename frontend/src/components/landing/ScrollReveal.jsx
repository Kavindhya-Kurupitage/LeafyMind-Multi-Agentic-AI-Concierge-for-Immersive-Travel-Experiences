import { motion, useReducedMotion } from "framer-motion";
import {
  fadeUp,
  slideLeft,
  slideRight,
  scaleIn,
  transition,
  viewport,
} from "../../utils/motion.js";

const VARIANTS = {
  up: fadeUp,
  left: slideLeft,
  right: slideRight,
  scale: scaleIn,
};

const TAGS = {
  div: motion.div,
  li: motion.li,
  section: motion.section,
  article: motion.article,
};

/**
 * Fade/slide children into view on scroll (Framer Motion + reduced-motion safe).
 */
function ScrollReveal({
  children,
  className = "",
  delay = 0,
  direction = "up",
  as = "div",
}) {
  const reduceMotion = useReducedMotion();
  const MotionTag = TAGS[as] ?? motion.div;
  const variants = VARIANTS[direction] ?? fadeUp;

  return (
    <MotionTag
      className={className}
      initial={reduceMotion ? "visible" : "hidden"}
      whileInView="visible"
      viewport={viewport}
      variants={variants}
      transition={{
        ...transition,
        delay: reduceMotion ? 0 : delay / 1000,
      }}
    >
      {children}
    </MotionTag>
  );
}

export default ScrollReveal;
