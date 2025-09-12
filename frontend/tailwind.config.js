/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: '#79db48', // Primary green (active buttons, user messages)
          secondary: '#ecf2e8', // Light gray-green (inactive buttons, AI messages)
          bg: '#f9fbf9', // Main background
          text: '#131a0f', // Dark text
          'text-muted': '#689254', // Muted text (labels)
        },
      },
      fontFamily: {
        sans: ['Manrope', 'Noto Sans', 'sans-serif'],
      },
      spacing: {
        18: '4.5rem',
        22: '5.5rem',
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
}
