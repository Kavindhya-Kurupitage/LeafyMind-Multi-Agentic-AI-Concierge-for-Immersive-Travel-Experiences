import { useEffect, useState } from "react";

import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";

import PageBackdrop from "../components/ui/PageBackdrop.jsx";
import { agentsAPI } from "../utils/api.js";

import AgentArtifactPanel from "../components/agents/AgentArtifactPanel.jsx";
import FoodGuideCard from "../components/recommendations/FoodGuideCard.jsx";
import PackageCard from "../components/recommendations/PackageCard.jsx";
import {
  resolveFoodArtifacts,
  resolvePackageList,
} from "../utils/agentArtifacts.js";

import AgentSidebar from "../components/agents/AgentSidebar.jsx";

import ToolActivityFeed from "../components/agents/ToolActivityFeed.jsx";

import ConciergeQuestion from "../components/guided/ConciergeQuestion.jsx";

import GuidedInputBar from "../components/guided/GuidedInputBar.jsx";

import GuidedStepper from "../components/guided/GuidedStepper.jsx";

import OptionChips from "../components/guided/OptionChips.jsx";

import LoadingSpinner from "../components/LoadingSpinner.jsx";

import MessageInput from "../components/chat/MessageInput.jsx";

import StreamingMessage from "../components/chat/StreamingMessage.jsx";

import TypingIndicator from "../components/chat/TypingIndicator.jsx";

import useAgentThread from "../hooks/useAgentThread.js";

import { useAuth } from "../store/authStore.jsx";



function WorkspaceMessage({ message }) {

  const isUser = message.role === "user";

  if (isUser) {

    return (

      <article className="flex justify-end">

        <p className="max-w-[85%] rounded-2xl rounded-tr-md bg-gold px-5 py-3 text-sm text-forest shadow-gold">

          {message.content}

        </p>

      </article>

    );

  }

  return (

    <article className="max-w-[88%]">

      <p className="whitespace-pre-wrap rounded-2xl rounded-tl-md border border-forest/15 bg-white px-5 py-3.5 text-sm leading-relaxed text-forest shadow-sm">

        {message.content}

      </p>

    </article>

  );

}



function AgentWorkspacePage() {

  const { agentId, threadId: threadIdParam } = useParams();

  const [searchParams] = useSearchParams();

  const feedbackSessionId = searchParams.get("session") || undefined;

  const navigate = useNavigate();

  const { user, logout } = useAuth();

  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [artifactOpen, setArtifactOpen] = useState(true);



  const {

    agentMeta,

    threadId,

    threads,

    messages,

    artifacts,

    guestProfile,

    toolActivity,

    isStreaming,

    streamingMessage,

    error,

    isLoading,

    sendMessage,

    submitGuided,

    skipGuided,

    startNewThread,

    selectThread,

    setError,

    journeyHint,

    clearJourneyHint,

    guidedMode,

    activeTurn,

    selection,

    setSelection,

    freeText,

    setFreeText,

    showHistory,

    setShowHistory,

  } = useAgentThread(agentId, threadIdParam, { feedbackSessionId });



  const [profileGate, setProfileGate] = useState(null);



  useEffect(() => {
    if (agentId === "food_guide" && resolveFoodArtifacts(artifacts)) {
      setArtifactOpen(true);
    }
  }, [agentId, artifacts]);

  useEffect(() => {

    agentsAPI

      .getJourney()

      .then((journey) => {

        const step = journey?.steps?.[agentId];

        if (step?.locked) {

          if (agentId === "feedback_collector") {

            setProfileGate(

              "Complete your profile and use a planning agent before feedback."

            );

          } else if (agentId !== "profile_builder") {

            setProfileGate("Complete your travel profile in Profile Builder first.");

          }

        } else {

          setProfileGate(null);

        }

      })

      .catch(() => setProfileGate(null));

  }, [agentId]);



  const handleLogout = async () => {

    await logout();

    navigate("/signin", { replace: true });

  };



  const handleNewThread = async () => {

    setSidebarOpen(false);

    const id = await startNewThread();

    if (id) navigate(`/agents/${agentId}/threads/${id}`, { replace: true });

  };



  const handleSelectThread = async (id) => {

    setSidebarOpen(false);

    await selectThread(id);

    navigate(`/agents/${agentId}/threads/${id}`, { replace: true });

  };



  if (isLoading && !agentMeta) {

    return <LoadingSpinner message="Opening agent workspace…" />;

  }



  const mergedArtifacts = { ...artifacts };

  if (artifacts.profile) mergedArtifacts.profile = artifacts.profile;

  const foodResults = agentId === "food_guide" ? resolveFoodArtifacts(mergedArtifacts) : null;
  const packageResults =
    agentId === "package_recommender" ? resolvePackageList(mergedArtifacts) : [];
  const showPlanningResults = packageResults.length > 0 || Boolean(foodResults);

  const showGuided = guidedMode && activeTurn && !profileGate;
  const hideOptionChips = activeTurn?.input_type === "confirm";

  const progress = activeTurn?.progress || { current: 1, total: 1 };

  const hasOptions = activeTurn?.options?.length > 0;



  return (

    <div className="relative flex h-screen max-h-screen overflow-hidden bg-mesh-cream">
      <PageBackdrop />

      <AgentSidebar

        agent={agentMeta}

        threads={threads}

        activeThreadId={threadId}

        onNewThread={handleNewThread}

        onSelectThread={handleSelectThread}

        user={user}

        onLogout={handleLogout}

        isOpen={sidebarOpen}

        onClose={() => setSidebarOpen(false)}

      />



      <div className="flex min-w-0 flex-1 flex-col">

        <header className="relative z-10 flex items-center justify-between gap-3 border-b border-cream-dark/60 bg-white/85 px-4 py-3 backdrop-blur-md lg:px-6">

          <div className="flex items-center gap-3">

            <button

              type="button"

              className="rounded-lg p-2 text-forest lg:hidden"

              onClick={() => setSidebarOpen(true)}

              aria-label="Open menu"

            >

              ☰

            </button>

            <div>

              <h1 className="font-display text-lg font-semibold text-forest">

                {agentMeta?.name || "Agent"}

              </h1>

              <p className="text-xs text-forest/50">

                {showGuided

                  ? "Tap your answers — typing is optional on every step"

                  : agentMeta?.tagline}

              </p>

            </div>

          </div>

          <button

            type="button"

            onClick={() => setArtifactOpen((o) => !o)}

            className="rounded-lg border border-cream-dark px-3 py-1.5 text-xs font-medium text-forest/70 lg:hidden"

          >

            {artifactOpen ? "Hide panel" : "Show outputs"}

          </button>

        </header>



        {showGuided && (

          <GuidedStepper

            current={progress.current}

            total={progress.total}

            label={agentMeta?.name}

          />

        )}



        <ToolActivityFeed activities={toolActivity} />



        {profileGate && (

          <div className="mx-4 mt-3 rounded-xl border border-gold/40 bg-gold/10 px-4 py-3 text-sm text-forest">

            {profileGate}{" "}

            <Link to="/hub" className="font-semibold underline">

              Back to dashboard

            </Link>

          </div>

        )}



        {journeyHint?.type === "profile_complete" && (

          <div className="mx-4 mt-3 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-forest/20 bg-forest/5 px-4 py-3 text-sm text-forest">

            <span>Your profile is complete. Choose a planning specialist on your dashboard.</span>

            <Link to="/hub" className="btn-gold shrink-0 px-4 py-2 text-xs" onClick={clearJourneyHint}>

              Go to dashboard

            </Link>

          </div>

        )}



        {journeyHint?.type === "planning_progress" && (

          <div className="mx-4 mt-3 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-forest/20 bg-forest/5 px-4 py-3 text-sm text-forest">

            <span>

              Specialist complete ({journeyHint.plannersDoneCount ?? 0}/3). Finish all planners on

              the dashboard to unlock your trip plan PDF.

            </span>

            <Link to="/hub" className="btn-gold shrink-0 px-4 py-2 text-xs" onClick={clearJourneyHint}>

              Go to dashboard

            </Link>

          </div>

        )}



        {journeyHint?.type === "trip_pack_ready" && (

          <div className="mx-4 mt-3 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-gold/40 bg-gold/10 px-4 py-3 text-sm text-forest">

            <span>

              All planners done! Download or email your trip plan PDF from the dashboard.

              {journeyHint.feedbackEmailSent

                ? " A feedback survey link was also sent."

                : ""}

            </span>

            <Link to="/hub" className="btn-gold shrink-0 px-4 py-2 text-xs" onClick={clearJourneyHint}>

              Get trip pack

            </Link>

          </div>

        )}



        {error && (

          <div className="auth-error mx-4 mt-3" role="alert">

            {error}

            <button type="button" className="ml-2 underline" onClick={() => setError(null)}>

              Dismiss

            </button>

          </div>

        )}



        <div className="flex min-h-0 flex-1">

          <section className="flex min-w-0 flex-1 flex-col">

            <div className="flex-1 overflow-y-auto px-4 py-6 lg:px-8">

              {showGuided ? (

                <div className="space-y-8">

                  <ConciergeQuestion

                    agentName={agentMeta?.name}

                    agentIcon={agentMeta?.icon}

                    turn={activeTurn}

                  />

                  {hasOptions && !hideOptionChips && (

                    <div className="mx-auto max-w-2xl">

                      <OptionChips

                        options={activeTurn.options}

                        inputType={activeTurn.input_type}

                        selected={selection}

                        onChange={setSelection}

                        disabled={isStreaming}

                      />

                    </div>

                  )}

                  <GuidedInputBar

                    turn={activeTurn}

                    selected={selection}

                    freeText={freeText}

                    onFreeTextChange={setFreeText}

                    onSubmit={submitGuided}

                    onSkip={skipGuided}

                    disabled={isStreaming}

                  />

                  {streamingMessage?.content && (
                    <div className="mx-auto max-w-2xl">
                      <StreamingMessage message={streamingMessage} />
                    </div>
                  )}
                  {packageResults.length > 0 && (
                    <div className="mx-auto max-w-2xl space-y-3">
                      <p className="text-xs font-semibold uppercase tracking-wider text-gold-dark">
                        Your matched cabana packages
                      </p>
                      {packageResults.map((pkg) => (
                        <PackageCard
                          key={pkg.package_name || pkg.name}
                          pkg={pkg}
                        />
                      ))}
                      <p className="text-xs text-forest/50">
                        Full details also appear in Agent outputs on the right.
                      </p>
                    </div>
                  )}
                  {foodResults && (
                    <div className="mx-auto max-w-2xl">
                      <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-gold-dark">
                        Your food guide — with photos
                      </p>
                      <FoodGuideCard food={foodResults} />
                      <p className="mt-2 text-xs text-forest/50">
                        Dish photos also appear in the panel on the right.
                      </p>
                    </div>
                  )}
                  {isStreaming && !streamingMessage?.content && !activeTurn && (
                    <TypingIndicator />
                  )}
                  {messages.length > 0 && (

                    <div className="mx-auto max-w-2xl border-t border-cream-dark pt-4">

                      <button

                        type="button"

                        className="text-xs font-medium text-forest/50 underline"

                        onClick={() => setShowHistory((h) => !h)}

                      >

                        {showHistory ? "Hide" : "Show"} conversation history

                      </button>

                      {showHistory && (

                        <div className="mt-4 space-y-4">

                          {messages.map((msg) => (

                            <WorkspaceMessage key={msg.id} message={msg} />

                          ))}

                        </div>

                      )}

                    </div>

                  )}

                </div>

              ) : (

                <>

                  {!streamingMessage && messages.length === 0 && (

                    <div className="mx-auto max-w-lg py-16 text-center">

                      <span className="text-5xl">{agentMeta?.icon}</span>

                      <h2 className="mt-4 font-display text-xl font-semibold text-forest">

                        {agentMeta?.name}

                      </h2>

                      <p className="mt-2 text-sm leading-relaxed text-forest/60">

                        {agentMeta?.description}

                      </p>

                      {guidedMode && (

                        <p className="mt-6 text-sm text-forest/45">

                          Loading your first question…

                        </p>

                      )}

                    </div>

                  )}

                  <div className="mx-auto max-w-2xl space-y-6">

                    {messages.map((msg) => (

                      <WorkspaceMessage key={msg.id} message={msg} />

                    ))}

                    {streamingMessage && <StreamingMessage message={streamingMessage} />}

                    {showPlanningResults && agentId === "package_recommender" && (
                      <div className="space-y-3">
                        <p className="text-xs font-semibold uppercase tracking-wider text-gold-dark">
                          Your matched cabana packages
                        </p>
                        {packageResults.map((pkg) => (
                          <PackageCard
                            key={pkg.package_name || pkg.name}
                            pkg={pkg}
                          />
                        ))}
                      </div>
                    )}

                    {showPlanningResults && foodResults && (
                      <FoodGuideCard food={foodResults} />
                    )}

                    {isStreaming && !streamingMessage?.content && <TypingIndicator />}

                  </div>

                </>

              )}

            </div>



            <footer className="border-t border-cream-dark bg-cream-light/80 px-4 py-4 lg:px-8">

              {!showGuided && (

                <MessageInput

                  onSend={sendMessage}

                  disabled={isStreaming || Boolean(profileGate)}

                  placeholder="Optional message…"

                />

              )}

            </footer>

          </section>



          <aside

            className={`flex shrink-0 flex-col border-l border-cream-dark bg-cream-light transition-all duration-300 ${

              artifactOpen ? "w-full sm:w-80 lg:w-96" : "hidden lg:flex lg:w-12"

            }`}

          >

            <header className="flex items-center justify-between border-b border-cream-dark px-4 py-3">

              {artifactOpen && (

                <h2 className="text-xs font-semibold uppercase tracking-wider text-forest/50">

                  Agent outputs

                </h2>

              )}

              <button

                type="button"

                onClick={() => setArtifactOpen((o) => !o)}

                className="ml-auto rounded-lg p-2 text-forest/60 hover:bg-cream-dark"

                aria-label={artifactOpen ? "Collapse" : "Expand"}

              >

                {artifactOpen ? "→" : "←"}

              </button>

            </header>

            {artifactOpen && (

              <div className="flex-1 overflow-y-auto p-4">

                <AgentArtifactPanel

                  agentId={agentId}

                  artifacts={mergedArtifacts}

                  guestProfile={guestProfile}

                />

              </div>

            )}

          </aside>

        </div>

      </div>

    </div>

  );

}



export default AgentWorkspacePage;


