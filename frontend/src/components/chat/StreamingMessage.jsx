import { useEffect, useState } from "react";
import AgentBadge from "./AgentBadge.jsx";

const REVEAL_MS = 12;

function StreamingMessage({ content, agent, phase, isComplete, onComplete }) {
  const [displayed, setDisplayed] = useState("");
  const [showBadge, setShowBadge] = useState(false);

  useEffect(() => {
    if (agent && content.length > 0) {
      setShowBadge(true);
    }
  }, [agent, content]);

  useEffect(() => {
    if (!content) {
      setDisplayed("");
      return undefined;
    }

    if (displayed.length >= content.length) {
      if (isComplete && onComplete) onComplete();
      return undefined;
    }

    const timer = setInterval(() => {
      setDisplayed((prev) => {
        const nextLen = Math.min(prev.length + 2, content.length);
        return content.slice(0, nextLen);
      });
    }, REVEAL_MS);

    return () => clearInterval(timer);
  }, [content, displayed.length, isComplete, onComplete]);

  useEffect(() => {
    if (isComplete) {
      setDisplayed(content);
    }
  }, [isComplete, content]);

  return (
    <section className="max-w-[88%] animate-slide-in-left">
      {showBadge && (
        <header className="mb-1.5 flex items-center gap-2">
          <AgentBadge agent={agent} />
          {phase && (
            <span className="text-[10px] uppercase tracking-wider text-forest/45">
              {phase.replace(/_/g, " ")}
            </span>
          )}
        </header>
      )}
      <article className="rounded-2xl rounded-tl-md border border-forest/20 bg-cream-light px-5 py-3.5 text-sm leading-relaxed text-forest shadow-sm">
        <span>{displayed}</span>
        {!isComplete && (
          <span
            className="ml-0.5 inline-block h-4 w-0.5 bg-forest/60 animate-stream-cursor"
            aria-hidden
          />
        )}
      </article>
    </section>
  );
}

export default StreamingMessage;
