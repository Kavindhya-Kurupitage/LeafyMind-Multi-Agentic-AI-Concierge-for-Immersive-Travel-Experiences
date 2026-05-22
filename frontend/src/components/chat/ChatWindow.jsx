import { useEffect, useRef } from "react";
import { getPhaseLabel } from "../../utils/chatHelpers.js";
import AgentBadge from "./AgentBadge.jsx";
import MessageInput from "./MessageInput.jsx";
import StreamingMessage from "./StreamingMessage.jsx";
import TypingIndicator from "./TypingIndicator.jsx";

function WelcomeIllustration() {
  return (
    <svg
      viewBox="0 0 120 120"
      className="mx-auto h-28 w-28 text-forest/25"
      aria-hidden
    >
      <ellipse cx="60" cy="95" rx="40" ry="8" fill="currentColor" opacity="0.3" />
      <path
        d="M60 20 C40 45 35 70 50 85 C55 75 65 75 70 85 C85 70 80 45 60 20Z"
        fill="currentColor"
        opacity="0.5"
      />
      <path
        d="M60 35 C50 50 48 62 55 72 M60 35 C70 50 72 62 65 72"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
        opacity="0.7"
      />
    </svg>
  );
}

function ChatMessage({ message }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <article className="flex justify-end animate-slide-in-right">
        <p className="max-w-[85%] rounded-2xl rounded-tr-md bg-gold px-5 py-3 text-sm leading-relaxed text-forest shadow-gold">
          {message.content}
        </p>
      </article>
    );
  }

  return (
    <article className="max-w-[88%] animate-slide-in-left">
      {message.agent && (
        <header className="mb-1.5">
          <AgentBadge agent={message.agent} />
        </header>
      )}
      <p className="rounded-2xl rounded-tl-md border border-forest/20 bg-cream-light px-5 py-3.5 text-sm leading-relaxed text-forest shadow-sm">
        {message.content}
      </p>
    </article>
  );
}

function ChatWindow({
  messages,
  streamingMessage,
  isStreaming,
  currentPhase,
  error,
  onSend,
  userName,
  feedbackMode = false,
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingMessage, isStreaming]);

  const isEmpty = messages.length === 0 && !streamingMessage;

  return (
    <section
      className={`flex h-full min-h-0 flex-1 flex-col ${
        feedbackMode ? "bg-[#faf8f4]" : "bg-cream"
      }`}
    >
      <header
        className={`shrink-0 border-b px-4 py-2.5 backdrop-blur-sm lg:px-6 ${
          feedbackMode
            ? "border-gold/25 bg-[#f5f0e8]/90"
            : "border-cream-dark bg-cream-light/80"
        }`}
      >
        <p className="text-center text-xs font-medium tracking-wide text-forest/70">
          {feedbackMode ? (
            <>
              <span className="text-gold-dark">💬</span> We&apos;d love to hear about your stay
            </>
          ) : (
            <>
              <span className="text-gold-dark">✦</span> {getPhaseLabel(currentPhase)}
              <span className="text-gold-dark"> ✦</span>
            </>
          )}
        </p>
      </header>

      <section className="flex-1 overflow-y-auto px-4 py-6 lg:px-6">
        {isEmpty && !isStreaming && (
          <section className="flex min-h-[50vh] flex-col items-center justify-center text-center animate-fade-in">
            <WelcomeIllustration />
            <h2 className="mt-6 font-display text-2xl font-semibold text-forest">
              Ayubowan{userName ? `, ${userName}` : ""}
            </h2>
            <p className="mt-3 max-w-md text-sm leading-relaxed text-forest/60">
              {feedbackMode
                ? "Share how your Leafy Cave experience was — your feedback helps us welcome future guests."
                : "Tell me about your dream Sri Lanka trip — dates, who you are travelling with, and what would make this stay unforgettable at Leafy Cave."}
            </p>
          </section>
        )}

        <section className="space-y-5">
          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}

          {streamingMessage && (
            <StreamingMessage
              content={streamingMessage.content}
              agent={streamingMessage.agent}
              phase={streamingMessage.phase}
              isComplete={!isStreaming}
            />
          )}

          {isStreaming && !streamingMessage?.content && <TypingIndicator />}
        </section>

        <span ref={bottomRef} className="block h-1" aria-hidden />
      </section>

      {error && (
        <p className="auth-error mx-4 mb-2 lg:mx-6" role="alert">
          {error}
        </p>
      )}

      <MessageInput onSend={onSend} isLoading={isStreaming} />
    </section>
  );
}

export default ChatWindow;
