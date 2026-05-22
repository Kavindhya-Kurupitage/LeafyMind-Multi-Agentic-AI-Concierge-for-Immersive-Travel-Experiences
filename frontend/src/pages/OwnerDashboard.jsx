import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import AppHeader from "../components/ui/AppHeader.jsx";
import PageBackdrop from "../components/ui/PageBackdrop.jsx";
import useOwnerData from "../hooks/useOwnerData.js";
import { useAuth } from "../store/authStore.jsx";

function SummaryCard({ label, value, subtext, accent }) {
  return (
    <article
      className={`rounded-xl border bg-white p-5 shadow-sm ${
        accent ? "border-gold/40 shadow-gold" : "border-cream-dark"
      }`}
    >
      <p className="text-xs font-semibold uppercase tracking-wider text-forest/50">{label}</p>
      <p className="mt-2 font-display text-3xl font-semibold text-forest">{value}</p>
      {subtext && <p className="mt-1 text-xs text-forest/55">{subtext}</p>}
    </article>
  );
}

function StarRating({ value }) {
  if (value == null) return <span className="text-forest/30">—</span>;
  return (
    <span className="font-medium text-gold-dark" title={`${value} / 5`}>
      {value}/5
    </span>
  );
}

function FeedbackTable({ rows, onToggleFlag }) {
  if (!rows?.length) {
    return (
      <p className="py-8 text-center text-sm text-forest/50">No feedback records yet.</p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead>
          <tr className="border-b border-cream-dark text-xs uppercase tracking-wider text-forest/45">
            <th className="px-4 py-3 font-semibold">Date</th>
            <th className="px-4 py-3 font-semibold">Package</th>
            <th className="px-4 py-3 font-semibold">Food</th>
            <th className="px-4 py-3 font-semibold">Itinerary</th>
            <th className="px-4 py-3 font-semibold">AI</th>
            <th className="px-4 py-3 font-semibold">Tags</th>
            <th className="px-4 py-3 font-semibold">Flag</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b border-cream-dark/60 hover:bg-cream-light/80">
              <td className="px-4 py-3 text-forest/70">
                {row.created_at
                  ? new Date(row.created_at).toLocaleDateString(undefined, {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })
                  : "—"}
              </td>
              <td className="px-4 py-3">
                <StarRating value={row.package_rating} />
              </td>
              <td className="px-4 py-3">
                <StarRating value={row.food_rating} />
              </td>
              <td className="px-4 py-3">
                <StarRating value={row.itinerary_rating} />
              </td>
              <td className="px-4 py-3">
                <StarRating value={row.ai_helpfulness_rating} />
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-1">
                  {(row.auto_tags || []).map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full bg-forest/10 px-2 py-0.5 text-[10px] text-forest/70"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </td>
              <td className="px-4 py-3">
                <button
                  type="button"
                  onClick={() => onToggleFlag(row.id)}
                  className={`rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase ${
                    row.flagged_for_review
                      ? "bg-red-100 text-red-700"
                      : "bg-cream-dark text-forest/50"
                  }`}
                >
                  {row.flagged_for_review ? "Flagged" : "Clear"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function OwnerDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { summary, flagged, isLoading, error, forbidden, refresh, toggleFlag } =
    useOwnerData();

  const handleLogout = async () => {
    await logout();
    navigate("/signin", { replace: true });
  };

  if (forbidden) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-cream px-4">
        <div className="max-w-md rounded-xl border border-cream-dark bg-white p-8 text-center shadow-luxury">
          <p className="text-forest">{error}</p>
          <Link to="/chat" className="btn-gold mt-6 inline-block">
            Go to guest chat
          </Link>
        </div>
      </div>
    );
  }

  const avgAi = summary?.avg_ratings?.ai ?? 0;

  return (
    <div className="relative min-h-screen bg-mesh-cream">
      <PageBackdrop />
      <AppHeader
        title="Operations Dashboard"
        subtitle={`Welcome back, ${user?.full_name || "Owner"}`}
        user={user}
        onLogout={handleLogout}
        homeTo="/owner"
      >
        <button
          type="button"
          onClick={refresh}
          className="rounded-xl border border-gold/40 px-4 py-2 text-sm text-gold transition hover:bg-gold/10"
        >
          Refresh
        </button>
        <Link
          to="/chat"
          className="rounded-xl border border-cream/20 bg-white/5 px-4 py-2 text-sm text-cream/80 backdrop-blur-sm transition hover:bg-white/10"
        >
          Guest chat
        </Link>
      </AppHeader>

      <motion.main
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative mx-auto max-w-7xl px-4 py-8 lg:px-6"
      >
        {error && (
          <p className="auth-error mb-6" role="alert">
            {error}
          </p>
        )}

        {isLoading && !summary ? (
          <p className="py-16 text-center text-forest/50">Loading dashboard…</p>
        ) : (
          <>
            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <SummaryCard
                label="Sessions this week"
                value={summary?.total_sessions_week ?? 0}
                subtext="New concierge conversations"
              />
              <SummaryCard
                label="Avg AI helpfulness"
                value={avgAi > 0 ? `${avgAi} ★` : "—"}
                subtext="Across all guest feedback"
                accent
              />
              <SummaryCard
                label="Flagged feedback"
                value={summary?.flagged_count ?? 0}
                subtext="Needs your attention"
                accent={(summary?.flagged_count ?? 0) > 0}
              />
              <SummaryCard
                label="Top package"
                value={summary?.most_recommended_package || "—"}
                subtext="Most suggested this week"
              />
            </section>

            <section className="mt-6">
              <article className="rounded-xl border border-gold/30 bg-gold/5 p-5">
                <p className="text-xs font-semibold uppercase tracking-wider text-gold-dark">
                  Live concierge
                </p>
                <p className="mt-1 font-display text-2xl font-semibold text-forest">
                  {summary?.active_sessions ?? 0}{" "}
                  <span className="text-base font-normal text-forest/60">
                    guest{summary?.active_sessions === 1 ? "" : "s"} chatting now
                  </span>
                </p>
              </article>
            </section>

            {(flagged?.length ?? 0) > 0 && (
              <section className="mt-8">
                <header className="mb-4 flex items-center justify-between">
                  <h2 className="font-display text-lg font-semibold text-forest">
                    Flagged — needs attention
                  </h2>
                  <span className="rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-700">
                    {flagged.length} item{flagged.length === 1 ? "" : "s"}
                  </span>
                </header>
                <article className="rounded-xl border-2 border-red-200 bg-red-50/50 p-4 shadow-sm">
                  <FeedbackTable rows={flagged} onToggleFlag={toggleFlag} />
                </article>
              </section>
            )}

            <section className="mt-8">
              <header className="mb-4">
                <h2 className="font-display text-lg font-semibold text-forest">
                  Recent feedback
                </h2>
                <p className="text-sm text-forest/55">
                  Package {summary?.avg_ratings?.package ?? 0} · Food{" "}
                  {summary?.avg_ratings?.food ?? 0} · Itinerary{" "}
                  {summary?.avg_ratings?.itinerary ?? 0} avg ratings
                </p>
              </header>
              <article className="rounded-xl border border-cream-dark bg-white shadow-sm">
                <FeedbackTable
                  rows={summary?.recent_feedback}
                  onToggleFlag={toggleFlag}
                />
              </article>
            </section>
          </>
        )}

        <p className="mt-8 text-center text-xs text-forest/40">
          Auto-refreshes every 30 seconds
        </p>
      </motion.main>
    </div>
  );
}

export default OwnerDashboard;
