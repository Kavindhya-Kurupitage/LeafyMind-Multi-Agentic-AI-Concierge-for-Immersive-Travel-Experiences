/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        forest: {
          DEFAULT: "#1a4731",
          light: "#2d6a4f",
          dark: "#143a28",
          darker: "#0c1612",
          muted: "#3d7a5c",
        },
        cream: {
          DEFAULT: "#f5f0e8",
          dark: "#e8e0d4",
          light: "#faf8f4",
        },
        gold: {
          DEFAULT: "#c9a84c",
          light: "#d4b96a",
          dark: "#a8873a",
        },
        cave: {
          DEFAULT: "#6f4e37",
          light: "#8a6550",
          dark: "#5a3f2c",
        },
      },
      fontFamily: {
        sans: ["Plus Jakarta Sans", "system-ui", "Segoe UI", "sans-serif"],
        display: ["Playfair Display", "Georgia", "serif"],
      },
      backgroundImage: {
        "mesh-cream":
          "radial-gradient(at 20% 20%, rgba(201,168,76,0.15) 0, transparent 50%), radial-gradient(at 80% 0%, rgba(45,106,79,0.12) 0, transparent 45%), radial-gradient(at 50% 100%, rgba(26,71,49,0.08) 0, transparent 50%)",
        "mesh-forest":
          "radial-gradient(at 15% 85%, rgba(45,106,79,0.5) 0, transparent 50%), radial-gradient(at 85% 15%, rgba(201,168,76,0.2) 0, transparent 45%)",
        "premium-gradient": "linear-gradient(135deg, #0c1612 0%, #1a4731 45%, #143a28 100%)",
      },
      animation: {
        "fade-in": "fadeIn 0.6s ease-out forwards",
        "fade-in-up": "fadeInUp 0.8s ease-out forwards",
        "slide-up": "slideUp 0.6s ease-out forwards",
        "slide-in-right": "slideInRight 0.5s ease-out forwards",
        "slide-in-left": "slideInLeft 0.5s ease-out forwards",
        "float": "float 6s ease-in-out infinite",
        "float-slow": "float 9s ease-in-out infinite",
        "ken-burns": "kenBurns 22s ease-out forwards",
        "shimmer": "shimmer 2.5s ease-in-out infinite",
        "bounce-soft": "bounceSoft 2s ease-in-out infinite",
        "pulse-glow": "pulseGlow 3s ease-in-out infinite",
        "typing-dot": "typingDot 1.2s ease-in-out infinite",
        "stream-cursor": "streamCursor 0.8s ease-in-out infinite",
        "gradient-shift": "gradientShift 8s ease infinite",
        "logo-pulse": "logoPulse 3s ease-in-out infinite",
        "glow": "glow 4s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        fadeInUp: {
          "0%": { opacity: "0", transform: "translateY(24px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideInRight: {
          "0%": { opacity: "0", transform: "translateX(12px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        slideInLeft: {
          "0%": { opacity: "0", transform: "translateX(-12px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-12px)" },
        },
        kenBurns: {
          "0%": { transform: "scale(1.05)" },
          "100%": { transform: "scale(1.15)" },
        },
        shimmer: {
          "0%, 100%": { opacity: "0.4" },
          "50%": { opacity: "1" },
        },
        bounceSoft: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(6px)" },
        },
        pulseGlow: {
          "0%, 100%": { opacity: "0.35", transform: "scale(1)" },
          "50%": { opacity: "0.65", transform: "scale(1.05)" },
        },
        gradientShift: {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
        typingDot: {
          "0%, 80%, 100%": { opacity: "0.25", transform: "translateY(0)" },
          "40%": { opacity: "1", transform: "translateY(-4px)" },
        },
        streamCursor: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.2" },
        },
        logoPulse: {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(201, 168, 76, 0.35)" },
          "50%": { boxShadow: "0 0 0 12px rgba(201, 168, 76, 0)" },
        },
        glow: {
          "0%, 100%": { opacity: "0.5" },
          "50%": { opacity: "1" },
        },
      },
      boxShadow: {
        luxury: "0 24px 48px -12px rgba(26, 71, 49, 0.18)",
        gold: "0 4px 20px -4px rgba(201, 168, 76, 0.35)",
        glass: "0 8px 32px -8px rgba(12, 22, 18, 0.12), inset 0 1px 0 rgba(255,255,255,0.6)",
        premium: "0 20px 60px -15px rgba(12, 22, 18, 0.25)",
      },
    },
  },
  plugins: [],
};
