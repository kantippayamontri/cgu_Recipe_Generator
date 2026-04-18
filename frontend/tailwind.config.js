/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#9d4f00',
        secondary: '#5d6936',
        surface: '#fffbff',
        'surface-container-low': '#fffbd8',
        'surface-container': '#f9f5cb',
        'surface-container-highest': '#efebad',
        'on-surface': '#3b390d',
        'on-surface-variant': '#686635',
        'secondary-container': '#e9f8b6',
        'outline-variant': '#bfbc82',
      },
      fontFamily: {
        headline: ['"Plus Jakarta Sans"', 'sans-serif'],
        body: ['Manrope', 'sans-serif'],
      },
      borderRadius: {
        DEFAULT: '1rem',
        lg: '2rem',
        xl: '3rem',
      },
    },
  },
  plugins: [],
}
