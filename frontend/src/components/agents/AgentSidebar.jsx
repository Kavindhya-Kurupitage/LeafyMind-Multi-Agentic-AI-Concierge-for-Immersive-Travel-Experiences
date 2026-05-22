import { Link } from "react-router-dom";
import LeafyCaveLogo from "../brand/LeafyCaveLogo.jsx";
import { formatSessionDate } from "../../utils/chatHelpers.js";

function AgentSidebar({
  agent,
  threads,
  activeThreadId,
  onNewThread,
  onSelectThread,
  user,
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
        className={`fixed bottom-0 left-0 right-0 z-50 flex max-h-[75vh] flex-col rounded-t-2xl bg-forest shadow-luxury transition-transform duration-300 lg:static lg:z-auto lg:h-full lg:max-h-none lg:w-64 lg:shrink-0 lg:rounded-none ${
          isOpen ? "translate-y-0" : "translate-y-full lg:translate-y-0"
        }`}
      >
        <header className="border-b border-forest-light/30 px-5 py-4">
          <div className="mb-4">
            <LeafyCaveLogo to="/hub" size="sm" variant="light" />
          </div>
          <Link to="/hub" className="text-[10px] font-medium uppercase tracking-[0.2em] text-gold/80 hover:text-gold">
            ← Agent Hub
          </Link>
          {agent && (
            <div className="mt-3 flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-gold/20 text-2xl">
                {agent.icon}
              </span>
              <span>
                <p className="font-display text-base font-semibold text-cream">{agent.name}</p>
                <p className="text-xs text-cream/55">{agent.tagline}</p>
              </span>
            </div>
          )}
        </header>

        {user && (
          <section className="flex items-center gap-3 border-b border-forest-light/20 px-5 py-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-gold text-sm font-semibold text-forest">
              {initial}
            </span>
            <span className="min-w-0">
              <p className="truncate text-sm font-medium text-cream">{user.full_name || "Guest"}</p>
              <p className="truncate text-xs text-cream/50">{user.email}</p>
            </span>
          </section>
        )}

        <section className="px-4 py-3">
          <button
            type="button"
            onClick={onNewThread}
            className="w-full rounded-lg border border-gold/50 bg-gold/10 py-2.5 text-sm font-semibold text-gold transition hover:bg-gold/20"
          >
            New conversation
          </button>
        </section>

        <nav className="flex-1 overflow-y-auto px-3 pb-2">
          <p className="px-2 pb-2 text-[10px] font-semibold uppercase tracking-wider text-cream/40">
            Conversations
          </p>
          {threads.length === 0 && (
            <p className="px-2 py-4 text-xs text-cream/50">No conversations yet</p>
          )}
          <ul className="space-y-1">
            {threads.map((thread) => (
              <li key={thread.id}>
                <button
                  type="button"
                  onClick={() => onSelectThread(thread.id)}
                  className={`w-full rounded-lg px-3 py-2.5 text-left transition ${
                    thread.id === activeThreadId
                      ? "bg-forest-light text-cream"
                      : "text-cream/80 hover:bg-forest-light/50"
                  }`}
                >
                  <p className="truncate text-sm font-medium">{thread.title}</p>
                  <p className="text-[10px] text-cream/45">
                    {formatSessionDate(thread.updated_at || thread.created_at)}
                    {thread.message_count > 0 && ` · ${thread.message_count} msgs`}
                  </p>
                </button>
              </li>
            ))}
          </ul>
        </nav>

        <footer className="space-y-2 border-t border-forest-light/20 p-4">
          <Link
            to="/chat"
            className="block w-full rounded-lg border border-cream/20 py-2 text-center text-sm text-cream/80 hover:bg-forest-light/40"
          >
            Full concierge mode
          </Link>
          <button
            type="button"
            onClick={onLogout}
            className="w-full rounded-lg py-2 text-sm text-cream/70 hover:bg-forest-light/40"
          >
            Logout
          </button>
        </footer>
      </aside>
    </>
  );
}

export default AgentSidebar;
