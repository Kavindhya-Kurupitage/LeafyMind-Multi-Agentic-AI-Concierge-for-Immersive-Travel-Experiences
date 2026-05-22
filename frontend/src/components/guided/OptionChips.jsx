import { motion } from "framer-motion";

export default function OptionChips({
  options = [],
  inputType = "single_select",
  selected = [],
  onChange,
  disabled = false,
}) {
  const isMulti = inputType === "multi_select";
  const isRating = inputType === "rating";

  const toggle = (id) => {
    if (disabled) return;
    if (isMulti) {
      const next = selected.includes(id) ? selected.filter((s) => s !== id) : [...selected, id];
      onChange(next);
      return;
    }
    onChange([id]);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, staggerChildren: 0.04 }}
      className={
        isRating
          ? "flex flex-wrap justify-center gap-2"
          : "grid gap-3 sm:grid-cols-2"
      }
      role={isMulti ? "group" : "radiogroup"}
      aria-label="Answer options"
    >
      {options.map((opt, index) => {
        const active = selected.includes(opt.id);
        return (
          <motion.button
            key={opt.id}
            type="button"
            disabled={disabled}
            role={isMulti ? "checkbox" : "radio"}
            aria-checked={active}
            onClick={() => toggle(opt.id)}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.04 }}
            whileHover={disabled ? {} : { scale: 1.02, y: -2 }}
            whileTap={disabled ? {} : { scale: 0.98 }}
            className={`chip-premium ${active ? "chip-premium-active" : ""} ${
              isRating ? "min-w-[4.5rem] text-center" : ""
            } ${disabled ? "opacity-50" : ""}`}
          >
            <span className="font-semibold">{opt.label}</span>
            {opt.description && (
              <span
                className={`mt-0.5 block text-xs ${active ? "text-cream/80" : "text-forest/55"}`}
              >
                {opt.description}
              </span>
            )}
          </motion.button>
        );
      })}
    </motion.div>
  );
}
