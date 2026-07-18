/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        "ink-navy": "var(--color-ink-navy)",
        "chart-cream": "var(--color-chart-cream)",
        "vital-teal": "var(--color-vital-teal)",
        "pulse-coral": "var(--color-pulse-coral)",
        graphite: "var(--color-graphite)",
        mist: "var(--color-mist)",
        "card-bg": "var(--color-card-bg)",
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "serif"],
        body: ["var(--font-plex-sans)", "sans-serif"],
        mono: ["var(--font-plex-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};
