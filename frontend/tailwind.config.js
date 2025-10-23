/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'montserrat': ['Montserrat', 'sans-serif'],
      },
      backgroundImage: {
        'linear-106': 'linear-gradient(106deg, #a21caf 0%, #64748b 100%)',
      },
    },
  },
  plugins: [],
}

