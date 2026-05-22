import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import LeafyCaveLogo from "../brand/LeafyCaveLogo.jsx";
import PackageCard from "../recommendations/PackageCard.jsx";
import FoodGuideCard from "../recommendations/FoodGuideCard.jsx";
import ItineraryTimeline from "../recommendations/ItineraryTimeline.jsx";
import { tripPackAPI } from "../../utils/api.js";
import { transition } from "../../utils/motion.js";

const PLANNER_STEPS = [
  { id: "package_recommender", label: "Package Recommender", icon: "📦" },
  { id: "food_guide", label: "Food Guide", icon: "🍛" },
  { id: "itinerary_planner", label: "Itinerary Planner", icon: "🗺" },
];

function PlannerChecklist({ journey, plannersDone }) {
  const doneMap = plannersDone || journey?.trip_pack_planners_done || {};
  const doneCount = PLANNER_STEPS.filter((s) => doneMap[s.id]).length;

  return (
    <div className="rounded-xl border border-forest/15 bg-white/80 p-4">
      <p className="text-sm font-medium text-forest">
        Trip pack progress: {doneCount} of 3 specialists complete
      </p>
      <ul className="mt-3 space-y-2">
        {PLANNER_STEPS.map((step) => {
          const done = Boolean(doneMap[step.id]);
          const threadId = journey?.steps?.[step.id]?.thread_id;
          const to = threadId
            ? `/agents/${step.id}/threads/${threadId}`
            : `/agents/${step.id}`;
          return (
            <li key={step.id} className="flex items-center justify-between gap-3 text-sm">
              <span className={done ? "text-forest" : "text-forest/55"}>
                {done ? "✓" : "○"} {step.icon} {step.label}
              </span>
              {!done && (
                <Link
                  to={to}
                  className="shrink-0 font-semibold text-gold-dark underline decoration-gold/40"
                >
                  Complete →
                </Link>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function TripPackPanel({ journey, onEmailSent }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [emailStatus, setEmailStatus] = useState(null);
  const [emailBusy, setEmailBusy] = useState(false);
  const [pdfBusy, setPdfBusy] = useState(false);
  const [expanded, setExpanded] = useState(true);

  const profileComplete = journey?.profile_complete;
  const ready = journey?.trip_pack_ready;
  const plannersDone = summary?.planners_done || journey?.trip_pack_planners_done;
  const emailSent = journey?.trip_pack_email_sent || summary?.trip_pack_email_sent;

  const loadSummary = useCallback(async () => {
    if (!profileComplete) return;
    setLoading(true);
    setError(null);
    try {
      const data = await tripPackAPI.getSummary();
      setSummary(data);
    } catch (err) {
      setError(err.message || "Could not load trip pack");
    } finally {
      setLoading(false);
    }
  }, [profileComplete]);

  useEffect(() => {
    loadSummary();
  }, [loadSummary, ready]);

  if (!profileComplete) return null;

  const packages = summary?.packages?.recommendations || [];
  const food = summary?.food || {};
  const guestEmail = summary?.guest_email;

  const handleDownloadPdf = async () => {
    if (!ready) return;
    setPdfBusy(true);
    setError(null);
    try {
      await tripPackAPI.downloadPdf(summary?.guest_name);
    } catch (err) {
      setError(err.message || "PDF download failed");
    } finally {
      setPdfBusy(false);
    }
  };

  const handleSendEmail = async () => {
    if (!ready) return;
    setEmailBusy(true);
    setEmailStatus(null);
    setError(null);
    try {
      const result = await tripPackAPI.sendEmail();
      setEmailStatus(result.message);
      if (result.sent && onEmailSent) {
        onEmailSent();
      }
    } catch (err) {
      setError(err.message || "Could not send email");
    } finally {
      setEmailBusy(false);
    }
  };

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={transition}
      className="relative mt-10 overflow-hidden rounded-2xl border border-gold/40 bg-gradient-to-br from-cream via-white to-cream-dark shadow-premium"
    >
      <div className="border-b border-gold/25 bg-forest px-6 py-5 text-cream md:px-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <LeafyCaveLogo to={null} size="sm" showWordmark={false} variant="light" />
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-gold/90">
                {ready ? "Trip pack ready" : "Your trip pack"}
              </p>
              <h2 className="mt-1 font-display text-2xl font-semibold">
                {ready
                  ? "Download or email your full plan"
                  : "Finish all 3 planners to unlock PDF & email"}
              </h2>
              <p className="mt-2 max-w-xl text-sm text-cream/75">
                {ready
                  ? "Branded PDF with packages, food photos, and your itinerary. This is separate from the feedback survey."
                  : "Complete Package, Food, and Itinerary below. The survey email is sent only after all three are done."}
              </p>
            </div>
          </div>
          {ready && (
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={handleDownloadPdf}
                disabled={pdfBusy}
                className="rounded-lg border border-gold/50 bg-gold px-4 py-2 text-sm font-semibold text-forest transition hover:bg-gold-light disabled:opacity-60"
              >
                {pdfBusy ? "Preparing PDF…" : "Download PDF"}
              </button>
              <button
                type="button"
                onClick={handleSendEmail}
                disabled={emailBusy || !guestEmail}
                title={!guestEmail ? "Add your email in Profile Builder first" : undefined}
                className="rounded-lg border border-cream/30 bg-cream/10 px-4 py-2 text-sm font-semibold text-cream transition hover:bg-cream/20 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {emailBusy ? "Sending…" : emailSent ? "Resend trip plan" : "Email my plan (PDF)"}
              </button>
              <button
                type="button"
                onClick={() => setExpanded((v) => !v)}
                className="rounded-lg border border-cream/20 px-3 py-2 text-sm text-cream/80 hover:bg-cream/10"
              >
                {expanded ? "Collapse" : "Expand"}
              </button>
            </div>
          )}
        </div>
        {ready && emailSent && !emailStatus && (
          <p className="mt-3 text-xs text-gold/90">Trip plan PDF was emailed previously.</p>
        )}
        {emailStatus && (
          <p className="mt-3 text-sm text-gold/90" role="status">
            {emailStatus}
          </p>
        )}
        {ready && !guestEmail && (
          <p className="mt-3 text-xs text-cream/60">
            Add your email in Profile Builder to use &quot;Email my plan&quot;.
          </p>
        )}
      </div>

      {error && (
        <div className="mx-6 mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 md:mx-8">
          {error}
        </div>
      )}

      <div className="space-y-6 px-6 py-6 md:px-8">
        {!ready && <PlannerChecklist journey={journey} plannersDone={plannersDone} />}

        {loading && (
          <p className="text-sm text-forest/60">Loading your trip pack…</p>
        )}

        {ready && expanded && !loading && summary && (
          <>
            <div>
              <h3 className="font-display text-lg font-semibold text-forest">Packages</h3>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                {packages.slice(0, 3).map((pkg) => (
                  <PackageCard key={pkg.package_name || pkg.name} pkg={pkg} />
                ))}
              </div>
            </div>
            <div>
              <h3 className="font-display text-lg font-semibold text-forest">Food guide</h3>
              <div className="mt-4">
                <FoodGuideCard food={food} />
              </div>
            </div>
            <div>
              <h3 className="font-display text-lg font-semibold text-forest">Itinerary</h3>
              <div className="mt-4">
                <ItineraryTimeline itinerary={summary.itinerary} />
              </div>
            </div>
          </>
        )}
      </div>
    </motion.section>
  );
}

export default TripPackPanel;
