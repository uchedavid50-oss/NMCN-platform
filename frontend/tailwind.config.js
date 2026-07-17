/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        "ink-navy": "#0F2438",
        "chart-cream": "#F7F5F0",
        "vital-teal": "#0E7C7B",
        "pulse-coral": "#E85D4E",
        graphite: "#3A4550",
        mist: "#D8E2E0",
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
