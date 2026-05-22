import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import LeafyCaveLogo from "../brand/LeafyCaveLogo.jsx";

/**
 * Premium app chrome for hub, workspace, and dashboard pages.
 */
export default function AppHeader({
  title,
  subtitle,
  user,
  onLogout,
  children,
  homeTo = "/hub",
}) {
  return (
    <motion.header
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="relative border-b border-forest-light/20 bg-gradient-to-r from-forest-darker via-forest to-forest-dark text-cream shadow-luxury"
    >
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(201,168,76,0.12),transparent_55%)]" />
      <div className="relative mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-5">
        <div className="flex min-w-0 flex-1 items-center gap-5">
          <LeafyCaveLogo to={homeTo} size="md" variant="light" />
          <div className="hidden h-10 w-px bg-cream/15 sm:block" />
          <div className="min-w-0">
            {title && (
              <h1 className="truncate font-display text-xl font-semibold md:text-2xl">{title}</h1>
            )}
            {subtitle && <p className="mt-0.5 text-sm text-cream/65">{subtitle}</p>}
          </div>
        </div>
        <nav className="flex shrink-0 items-center gap-2 sm:gap-3">
          {children}
          {user?.role === "owner" && (
            <Link
              to="/owner"
              className="hidden rounded-xl border border-cream/20 bg-white/5 px-4 py-2 text-sm font-medium backdrop-blur-sm transition hover:bg-white/10 sm:inline-block"
            >
              Owner
            </Link>
          )}
          {onLogout && (
            <button
              type="button"
              onClick={onLogout}
              className="rounded-xl border border-cream/20 bg-white/5 px-4 py-2 text-sm text-cream/85 backdrop-blur-sm transition hover:bg-white/10"
            >
              Logout
            </button>
          )}
        </nav>
      </div>
    </motion.header>
  );
}
