/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "Inter Variable",
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
      colors: {
        brand: {
          50: "#eef4ff",
          100: "#dbe6fe",
          200: "#bfd3fe",
          300: "#93b4fd",
          400: "#608cfa",
          500: "#3b6bf6",
          600: "#254deb",
          700: "#1d3ad8",
          800: "#1e32af",
          900: "#1e2f8a",
          950: "#171f54",
        },
        surface: "rgb(var(--surface) / <alpha-value>)",
        raised: "rgb(var(--raised) / <alpha-value>)",
        sunken: "rgb(var(--sunken) / <alpha-value>)",
        line: "rgb(var(--line) / <alpha-value>)",
        content: "rgb(var(--content) / <alpha-value>)",
        muted: "rgb(var(--muted) / <alpha-value>)",
        ink: {
          50: "#f7f8fa",
          100: "#eef0f4",
          200: "#dfe3ea",
          300: "#c6ccd8",
          400: "#97a1b3",
          500: "#6b7689",
          600: "#505a6b",
          700: "#3d4553",
          800: "#232a35",
          900: "#141a23",
          950: "#0b0f16",
        },
      },
      boxShadow: {
        card: "0 1px 2px rgba(15,23,42,.04), 0 8px 24px -12px rgba(15,23,42,.12)",
        lift: "0 2px 6px rgba(15,23,42,.06), 0 24px 48px -24px rgba(15,23,42,.25)",
      },
      borderRadius: { xl2: "1rem" },
      keyframes: {
        "fade-up": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
        "indeterminate": {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(250%)" },
        },
      },
      animation: {
        "fade-up": "fade-up .28s cubic-bezier(.2,.7,.3,1) both",
        shimmer: "shimmer 1.6s infinite",
        indeterminate: "indeterminate 1.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
