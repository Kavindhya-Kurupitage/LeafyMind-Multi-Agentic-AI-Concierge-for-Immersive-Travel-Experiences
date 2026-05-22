import { Link } from "react-router-dom";
import { formatSessionDate } from "../../utils/chatHelpers.js";

function LeafLogo({ className }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden>
      <path
        d="M16 4 C10 12 8 18 12 24 C14 20 18 20 20 24 C24 18 22 12 16 4Z"
        fill="currentColor"
      />
    </svg>
  );
}

function Sidebar({
  user,
  sessions,
  activeSessionId,
  onNewSession,
  onSelectSession,
  onLogout,
  isOpen,
  onClose,
}) {
  const initial = (user?.full_name || user?.email || "?").charAt(0).toUpperCase();

  return (
    <>
      {isOpen && (
        <button
          type="button"
          className="fixed inset-0 z-40 bg-forest/50 lg:hidden"
          onClick={onClose}
          aria-label="Close menu"
        />
      )}

      <aside
        className={`fixed bottom-0 left-0 right-0 z-50 flex max-h-[70vh] flex-col rounded-t-2xl bg-forest shadow-luxury transition-transform duration-300 lg:static lg:z-auto lg:h-full lg:max-h-none lg:w-60 lg:shrink-0 lg:rounded-none ${
          isOpen ? "translate-y-0" : "translate-y-full lg:translate-y-0"
        }`}
      >
        <header className="flex items-center gap-3 border-b border-forest-light/30 px-5 py-5">
          <LeafLogo className="h-8 w-8 text-gold" />
          <span className="block">
            <p className="text-[10px] font-medium uppercase tracking-[0.2em] text-gold/80">
              Leafy Cave
            </p>
            <p className="font-display text-lg font-semibold text-cream">LeafyMind</p>
          </span>
        </header>

        {user && (
          <section className="flex items-center gap-3 border-b border-forest-light/20 px-5 py-4">
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-gold font-semibold text-forest">
              {initial}
            </span>
            <span className="block min-w-0">
              <p className="truncate text-sm font-medium text-cream">
                {user.full_name || "Guest"}
              </p>
              <p className="truncate text-xs text-cream/60">{user.email}</p>
            </span>
          </section>
        )}

        <section className="space-y-2 px-4 py-4">
          <Link
            to="/hub"
            className="mb-2 block w-full rounded-lg border border-cream/25 py-2.5 text-center text-sm font-semibold text-cream/90 transition hover:bg-forest-light/50"
          >
            Agent Hub
          </Link>
          <button
            type="button"
            onClick={onNewSession}
            className="w-full rounded-lg border border-gold/50 bg-gold/10 py-2.5 text-sm font-semibold text-gold transition hover:bg-gold/20"
          >
            Start New Trip
          </button>
          {user?.role === "owner" && (
            <Link
              to="/owner"
              className="block w-full rounded-lg border border-cream/20 py-2.5 text-center text-sm font-semibold text-cream/90 transition hover:bg-forest-light/50"
            >
              Owner dashboard
            </Link>
          )}
        </section>

        <nav className="flex-1 overflow-y-auto px-3 pb-2">
          <p className="px-2 pb-2 text-[10px] font-semibold uppercase tracking-wider text-cream/40">
            Past conversations
          </p>
          {sessions.length === 0 && (
            <p className="px-2 py-4 text-xs text-cream/50">No past trips yet</p>
          )}
          <ul className="space-y-1">
            {sessions.map((session) => (
              <li key={session.id}>
                <button
                  type="button"
                  onClick={() => onSelectSession(session.id)}
                  className={`w-full rounded-lg px-3 py-2.5 text-left transition ${
                    session.id === activeSessionId
                      ? "bg-forest-light text-cream"
                      : "text-cream/80 hover:bg-forest-light/50"
                  }`}
                >
                  <p className="truncate text-sm font-medium">{session.preview}</p>
                  <p className="text-[10px] text-cream/45">
                    {formatSessionDate(session.createdAt)}
                  </p>
                </button>
              </li>
            ))}
          </ul>
        </nav>

        <footer className="border-t border-forest-light/20 p-4">
          <button
            type="button"
            onClick={onLogout}
            className="w-full rounded-lg py-2.5 text-sm text-cream/70 transition hover:bg-forest-light/40 hover:text-cream"
          >
            Logout
          </button>
        </footer>
      </aside>
    </>
  );
}

export default Sidebar;
