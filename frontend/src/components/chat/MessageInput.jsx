import { useCallback, useEffect, useRef, useState } from "react";

const MAX_CHARS = 2000;
const MAX_LINES = 4;
const LINE_HEIGHT = 24;

function MessageInput({
  onSend,
  isLoading,
  disabled,
  placeholder = "Ask about stays, food, temples, or your dream itinerary…",
}) {
  const [text, setText] = useState("");
  const textareaRef = useRef(null);

  const remaining = MAX_CHARS - text.length;
  const canSend = text.trim().length > 0 && !isLoading && !disabled;

  const resizeTextarea = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    const maxHeight = LINE_HEIGHT * MAX_LINES;
    el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`;
  }, []);

  useEffect(() => {
    resizeTextarea();
  }, [text, resizeTextarea]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!canSend) return;
    onSend(text.trim());
    setText("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleChange = (e) => {
    const value = e.target.value.slice(0, MAX_CHARS);
    setText(value);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-cream-dark bg-white px-4 py-3 lg:px-6"
    >
      {isLoading && (
        <p className="mb-2 text-center text-xs font-medium text-forest/50">
          AI is thinking…
        </p>
      )}
      <fieldset className="flex items-end gap-3 border-0 p-0 m-0 min-w-0">
        <label className="relative flex-1 block">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            rows={1}
            disabled={isLoading || disabled}
            className="input-field chat-textarea min-h-[48px] w-full resize-none overflow-y-auto py-3 pr-14 leading-6"
            aria-label="Message"
          />
          <span
            className={`pointer-events-none absolute bottom-3 right-3 text-[10px] tabular-nums ${
              remaining < 100 ? "text-red-600" : "text-forest/35"
            }`}
          >
            {remaining}
          </span>
        </label>
        <button
          type="submit"
          disabled={!canSend}
          className="btn-gold shrink-0 px-5 py-3 text-sm"
          aria-label="Send message"
        >
          Send
        </button>
      </fieldset>
    </form>
  );
}

export default MessageInput;
