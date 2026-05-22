import { Link } from "react-router-dom";
import { motion, useReducedMotion } from "framer-motion";
import LeafyCaveLogo from "../brand/LeafyCaveLogo.jsx";
import { useAuth } from "../../store/authStore.jsx";
import { useNavScrolled } from "../../hooks/useScrollReveal.js";
import { fadeIn, transition } from "../../utils/motion.js";

function LandingNav() {
  const { isAuthenticated, user } = useAuth();
  const scrolled = useNavScrolled(40);
  const reduceMotion = useReducedMotion();

  return (
    <motion.header
      className="fixed inset-x-0 top-0 z-50 border-b backdrop-blur-xl"
      initial={reduceMotion ? false : { y: -24, opacity: 0 }}
      animate={{
        y: 0,
        opacity: 1,
        paddingTop: scrolled ? 12 : 16,
        paddingBottom: scrolled ? 12 : 16,
        borderColor: scrolled ? "rgba(255,255,255,0.12)" : "transparent",
        backgroundColor: scrolled ? "rgba(12, 22, 18, 0.92)" : "rgba(12, 22, 18, 0.35)",
        boxShadow: scrolled
          ? "0 24px 48px -12px rgba(26, 71, 49, 0.35)"
          : "0 0 0 0 transparent",
      }}
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 lg:px-8">
        <motion.div
          variants={fadeIn}
          initial="hidden"
          animate="visible"
          transition={{ ...transition, delay: 0.1 }}
        >
          <LeafyCaveLogo to="/" size="md" variant="light" />
        </motion.div>

        <motion.nav
          className="hidden items-center gap-8 md:flex"
          variants={fadeIn}
          initial="hidden"
          animate="visible"
          transition={{ ...transition, delay: 0.2 }}
        >
          {["#agents", "#journey", "#features"].map((href, i) => (
            <motion.a
              key={href}
              href={href}
              className="text-sm text-cream/75"
              whileHover={reduceMotion ? {} : { color: "#c9a84c", y: -2 }}
              transition={{ duration: 0.2 }}
            >
              {["AI Agents", "Your Journey", "Features"][i]}
            </motion.a>
          ))}
        </motion.nav>

        <motion.div
          className="flex items-center gap-2 sm:gap-3"
          variants={fadeIn}
          initial="hidden"
          animate="visible"
          transition={{ ...transition, delay: 0.3 }}
        >
          {isAuthenticated ? (
            <>
              {user?.role === "owner" && (
                <Link
                  to="/owner"
                  className="btn-row hidden !min-w-0 border border-gold/40 bg-transparent !px-4 text-sm font-medium text-gold hover:bg-gold/10 sm:inline-flex"
                >
                  Dashboard
                </Link>
              )}
              <motion.div whileHover={reduceMotion ? {} : { scale: 1.04 }} whileTap={{ scale: 0.98 }}>
                <Link to="/hub" className="btn-gold btn-row !min-w-[9.5rem] text-sm">
                  Open Concierge
                </Link>
              </motion.div>
            </>
          ) : (
            <>
              <Link
                to="/signin"
                className="btn-row hidden !min-w-[5.5rem] border-0 bg-transparent !px-4 text-sm font-medium text-cream/85 hover:bg-white/10 hover:text-cream sm:inline-flex"
              >
                Sign in
              </Link>
              <motion.div whileHover={reduceMotion ? {} : { scale: 1.04 }} whileTap={{ scale: 0.98 }}>
                <Link to="/register" className="btn-gold btn-row !min-w-[9.5rem] text-sm">
                  Start planning
                </Link>
              </motion.div>
            </>
          )}
        </motion.div>
      </div>
    </motion.header>
  );
}

export default LandingNav;
