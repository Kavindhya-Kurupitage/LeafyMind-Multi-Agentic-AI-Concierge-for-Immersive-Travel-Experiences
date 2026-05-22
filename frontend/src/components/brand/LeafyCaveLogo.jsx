import { useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";

const SOURCES = ["/logo.png", "/logo.svg", "/leaf.svg"];

/**
 * Leafy Cave brand mark — prefers logo.png when present in /public.
 */
export default function LeafyCaveLogo({
  size = "md",
  showWordmark = true,
  subtitle = "LeafyMind",
  to = "/",
  className = "",
  animate = true,
  variant = "dark",
}) {
  const titleColor = variant === "light" ? "text-cream" : "text-forest";
  const subColor = variant === "light" ? "text-gold/90" : "text-gold-dark";
  const [srcIndex, setSrcIndex] = useState(0);
  const src = SOURCES[Math.min(srcIndex, SOURCES.length - 1)];

  const sizes = {
    sm: { img: "h-9 w-9", title: "text-base", sub: "text-[9px]" },
    md: { img: "h-11 w-11", title: "text-lg", sub: "text-[10px]" },
    lg: { img: "h-14 w-14", title: "text-xl", sub: "text-[10px]" },
    xl: { img: "h-20 w-20", title: "text-2xl", sub: "text-xs" },
    hero: { img: "h-24 w-24", title: "text-3xl", sub: "text-xs" },
  };
  const s = sizes[size] || sizes.md;

  const handleError = () => {
    if (srcIndex < SOURCES.length - 1) setSrcIndex((i) => i + 1);
  };

  const img = (
    <motion.img
      src={src}
      alt="Leafy Cave"
      onError={handleError}
      className={`${s.img} rounded-full bg-cream/95 object-contain p-1 shadow-gold ring-2 ring-gold/30`}
      whileHover={animate ? { scale: 1.06, rotate: 2 } : undefined}
      transition={{ type: "spring", stiffness: 400, damping: 18 }}
    />
  );

  const content = (
    <span className={`inline-flex items-center gap-3 ${className}`}>
      {img}
      {showWordmark && (
        <span className="text-left leading-tight">
          <span className={`block font-display font-semibold tracking-tight ${titleColor} ${s.title}`}>
            Leafy Cave
          </span>
          {subtitle && (
            <span
              className={`block font-medium uppercase tracking-[0.22em] ${subColor} ${s.sub}`}
            >
              {subtitle}
            </span>
          )}
        </span>
      )}
    </span>
  );

  if (to) {
    return (
      <Link to={to} className="group transition-opacity hover:opacity-95">
        {content}
      </Link>
    );
  }
  return content;
}
