/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b1020",
        panel: "#121a2b",
        line: "#25324a",
        accent: "#38bdf8",
        ok: "#34d399",
        warn: "#f59e0b",
        danger: "#fb7185",
      },
    },
  },
  plugins: [],
};
