/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          base: "#0f1117",
          surface: "#161b27",
          elevated: "#1e2535",
          border: "#2a3347",
        },
        accent: {
          cyan: "#38bdf8",
          violet: "#818cf8",
          amber: "#fbbf24",
          red: "#f87171",
          green: "#4ade80",
          muted: "#64748b",
        },
        text: {
          primary: "#e2e8f0",
          secondary: "#94a3b8",
          dim: "#475569",
        },
      },
      fontFamily: {
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
        ui: ["Inter", "DM Sans", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
