import { useState } from "react";

/**
 * Optional free text + Continue for hybrid guided steps.
 */
export default function GuidedInputBar({
  turn,
  selected = [],
  freeText = "",
  onFreeTextChange,
  onSubmit,
  onSkip,
  disabled = false,
}) {
  const [showText, setShowText] = useState(false);
  if (!turn) return null;

  const {
    input_type: inputType,
    allow_free_text: allowFreeText,
    free_text_label: freeTextLabel,
    allow_skip: allowSkip,
    min_selections: minSelections = 0,
    is_confirm: isConfirm,
  } = turn;

  const isTextOnly = inputType === "text" && (!turn.options || turn.options.length === 0);
  const needsSelection =
    inputType !== "text" && minSelections > 0 && selected.length < minSelections;
  const canContinue =
    isTextOnly ||
    isConfirm ||
    inputType === "text" ||
    selected.length > 0 ||
    (allowFreeText && freeText.trim().length > 0) ||
    (allowSkip && selected.includes("skip"));

  const primaryLabel = isConfirm
    ? turn.options?.[0]?.label || "Continue"
    : inputType === "text"
      ? "Continue"
      : "Continue";

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      {(allowFreeText || isTextOnly) && (
        <div>
          {!isTextOnly && !showText && (
            <button
              type="button"
              className="text-xs font-medium text-forest/55 underline hover:text-forest"
              onClick={() => setShowText(true)}
            >
              Type instead (optional)
            </button>
          )}
          {(showText || isTextOnly || allowFreeText) && (
            <label className="block">
              <span className="mb-1.5 block text-xs text-forest/50">
                {freeTextLabel || "Anything else? (optional)"}
              </span>
              <input
                type={inputType === "text" && freeTextLabel?.toLowerCase().includes("email") ? "email" : "text"}
                value={freeText}
                onChange={(e) => onFreeTextChange(e.target.value)}
                disabled={disabled}
                placeholder={freeTextLabel || ""}
                className="w-full rounded-xl border border-forest/15 bg-white px-4 py-2.5 text-sm text-forest focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold/40"
              />
            </label>
          )}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          disabled={disabled || !canContinue || needsSelection}
          onClick={() => onSubmit()}
          className="btn-gold px-6 py-2.5 text-sm disabled:cursor-not-allowed disabled:opacity-50"
        >
          {primaryLabel}
        </button>
        {allowSkip && (
          <button
            type="button"
            disabled={disabled}
            onClick={() => onSkip?.()}
            className="text-sm font-medium text-forest/55 hover:text-forest"
          >
            Skip
          </button>
        )}
      </div>
    </div>
  );
}
