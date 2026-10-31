/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#060b19',
          900: '#0b132b',
          800: '#131f42',
          700: '#1c2d5a',
        },
      },
    },
  },
  plugins: [],
};

