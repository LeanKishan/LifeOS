/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["Sora", "Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        ink: "rgb(var(--ink) / <alpha-value>)",
        elev: "rgb(var(--elev) / <alpha-value>)",
        surface: "rgb(var(--surface) / <alpha-value>)",
        "surface-2": "rgb(var(--surface-2) / <alpha-value>)",
        line: "rgb(var(--line) / <alpha-value>)",
        content: "rgb(var(--content) / <alpha-value>)",
        muted: "rgb(var(--muted) / <alpha-value>)",
        faint: "rgb(var(--faint) / <alpha-value>)",
        brand: {
          DEFAULT: "rgb(var(--brand) / <alpha-value>)",
          hi: "rgb(var(--brand-hi) / <alpha-value>)",
          lo: "rgb(var(--brand-lo) / <alpha-value>)",
        },
        violetish: "rgb(var(--violet) / <alpha-value>)",
      },
      borderColor: {
        DEFAULT: "rgb(var(--line) / 0.1)",
      },
      borderRadius: {
        lg: "0.625rem",
        xl: "0.875rem",
        "2xl": "1.125rem",
        "3xl": "1.5rem",
      },
      boxShadow: {
        card: "0 1px 2px rgb(0 0 0 / 0.28), 0 10px 30px -14px rgb(0 0 0 / 0.6)",
        pop: "0 24px 60px -12px rgb(0 0 0 / 0.7)",
        glow: "0 0 0 1px rgb(var(--brand) / 0.35), 0 12px 34px -8px rgb(var(--brand) / 0.5)",
        "glow-sm": "0 6px 20px -8px rgb(var(--brand) / 0.55)",
      },
      keyframes: {
        "fade-in-up": {
          from: { opacity: "0", transform: "translateY(10px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "scale-in": {
          from: { opacity: "0", transform: "scale(0.96)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        "slide-in-right": {
          from: { opacity: "0", transform: "translateX(16px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
        shimmer: { "100%": { transform: "translateX(220%)" } },
        aurora: {
          "0%,100%": { transform: "translate3d(0,0,0) scale(1)" },
          "33%": { transform: "translate3d(6%,-4%,0) scale(1.12)" },
          "66%": { transform: "translate3d(-5%,5%,0) scale(0.94)" },
        },
      },
      animation: {
        "fade-in-up": "fade-in-up 0.5s cubic-bezier(0.22,1,0.36,1) backwards",
        "scale-in": "scale-in 0.26s cubic-bezier(0.22,1,0.36,1)",
        "slide-in-right": "slide-in-right 0.35s cubic-bezier(0.22,1,0.36,1)",
        aurora: "aurora 22s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
