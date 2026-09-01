/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#2f4858',
          light: '#eef2f4',
        },
      },
    },
  },
  plugins: [],
}
