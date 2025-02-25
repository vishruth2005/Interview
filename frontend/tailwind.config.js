/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "var(--primary)",
        'primary-dark': "var(--primary-dark)",
      },
    },
  },
  plugins: [require("@tailwindcss/forms")],
} 