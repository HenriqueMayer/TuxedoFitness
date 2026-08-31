/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './accounts/**/*.py',
    './dashboard/**/*.py',
    './integrations/**/*.py',
    './training/**/*.py',
    './static/js/**/*.js',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cream: { DEFAULT: '#FAF8F3', dark: '#EBE7DE' },
        forest: { DEFAULT: '#1A2E26', light: '#2A4338', deep: '#101E18' },
        caramel: { DEFAULT: '#B88A59', light: '#D4AD86', ink: '#8A5A2F' },
        positive: { DEFAULT: '#176B52', light: '#64D8B1' },
        negative: { DEFAULT: '#B42318', light: '#FF8A80' },
        attention: { DEFAULT: '#A65300', light: '#FFB45C' },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
};
