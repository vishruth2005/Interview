export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#9BC53D',
        secondary: '#FDE5E5',
      },
      animation :{
        'gradient-x':'gradient-x 15s ease infinite',
      },
    },
  },
  plugins: [],
}