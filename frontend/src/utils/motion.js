/** Shared Framer Motion variants for the landing page. */

export const easeOut = [0.22, 1, 0.36, 1];

export const transition = { duration: 0.65, ease: easeOut };

export const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  visible: { opacity: 1, y: 0 },
};

export const fadeIn = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
};

export const slideLeft = {
  hidden: { opacity: 0, x: -48 },
  visible: { opacity: 1, x: 0 },
};

export const slideRight = {
  hidden: { opacity: 0, x: 48 },
  visible: { opacity: 1, x: 0 },
};

export const scaleIn = {
  hidden: { opacity: 0, scale: 0.9 },
  visible: { opacity: 1, scale: 1 },
};

export const staggerContainer = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.1, delayChildren: 0.15 },
  },
};

export const viewport = { once: true, margin: "-60px" };

export const floatOrb = (delay = 0) => ({
  y: [0, -14, 0],
  transition: {
    duration: 5 + delay,
    repeat: Infinity,
    ease: "easeInOut",
    delay,
  },
});

export const spring = { type: "spring", stiffness: 320, damping: 28 };

export const cardHover = {
  rest: { scale: 1, y: 0 },
  hover: { scale: 1.02, y: -6, transition: spring },
  tap: { scale: 0.98 },
};

export const pageEnter = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: easeOut } },
};
