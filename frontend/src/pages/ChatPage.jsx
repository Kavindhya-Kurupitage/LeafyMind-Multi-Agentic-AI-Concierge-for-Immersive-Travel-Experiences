import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import ChatWindow from "../components/chat/ChatWindow.jsx";
import InfoPanel from "../components/chat/InfoPanel.jsx";
import Sidebar from "../components/layout/Sidebar.jsx";
import useChat from "../hooks/useChat.js";
import { useAuth } from "../store/authStore.jsx";

function ChatPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [infoOpen, setInfoOpen] = useState(true);

  const feedbackModeFromUrl = searchParams.get("mode") === "feedback";
  const sessionFromUrl = searchParams.get("session");
  const autoStart = !(feedbackModeFromUrl && sessionFromUrl);

  const userId = user?.id;
  const firstName = user?.full_name?.split(" ")[0];

  const {
    messages,
    isStreaming,
    currentPhase,
    sessionId,
    recommendations,
    pastSessions,
    error,
    streamingMessage,
    startSession,
    sendMessage,
    selectSession,
    enterFeedbackMode,
    feedbackMode,
    setError,
  } = useChat(userId, { autoStart });

  const isFeedbackExperience = feedbackMode || feedbackModeFromUrl;

  useEffect(() => {
    if (feedbackModeFromUrl && sessionFromUrl && userId) {
      enterFeedbackMode(sessionFromUrl);
    }
  }, [feedbackModeFromUrl, sessionFromUrl, userId, enterFeedbackMode]);

  const handleLogout = async () => {
    await logout();
    navigate("/signin", { replace: true });
  };

  const handleNewSession = async () => {
    setSidebarOpen(false);
    setError(null);
    try {
      await startSession();
    } catch (err) {
      setError(err.message || "Could not start a new session");
    }
  };

  const handleSelectSession = async (id) => {
    setSidebarOpen(false);
    await selectSession(id);
  };

  return (
    <div
      className={`flex h-screen max-h-screen overflow-hidden ${
        isFeedbackExperience ? "bg-[#faf8f4]" : "bg-cream"
      }`}
    >
      <Sidebar
        user={user}
        sessions={pastSessions}
        activeSessionId={sessionId}
        onNewSession={handleNewSession}
        onSelectSession={handleSelectSession}
        onLogout={handleLogout}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-cream-dark bg-white px-4 py-3 lg:hidden">
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            className="rounded-lg p-2 text-forest hover:bg-cream-dark"
            aria-label="Open menu"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>
          <p className="font-display text-sm font-semibold text-forest">
            {isFeedbackExperience ? "Share feedback" : "LeafyMind"}
          </p>
          <button
            type="button"
            onClick={() => setInfoOpen((v) => !v)}
            className="rounded-lg p-2 text-forest hover:bg-cream-dark"
            aria-label="Toggle recommendations"
            disabled={isFeedbackExperience}
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
          </button>
        </header>

        <section className="flex min-h-0 flex-1">
          <ChatWindow
            messages={messages}
            streamingMessage={streamingMessage}
            isStreaming={isStreaming}
            currentPhase={currentPhase}
            error={error}
            onSend={sendMessage}
            userName={firstName}
            feedbackMode={isFeedbackExperience}
          />

          {!isFeedbackExperience && (
            <InfoPanel
              recommendations={recommendations}
              isOpen={infoOpen}
              onToggle={() => setInfoOpen((v) => !v)}
            />
          )}
        </section>

        <footer className="border-t border-cream-dark bg-white px-4 py-2 lg:hidden">
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            className="w-full rounded-lg py-2 text-center text-xs font-medium text-forest/60"
          >
            Menu & past trips
          </button>
        </footer>
      </main>
    </div>
  );
}

export default ChatPage;
