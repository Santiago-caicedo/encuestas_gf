/** @type {import('tailwindcss').Config} */
module.exports = {
  // Rutas donde Tailwind busca clases. Incluye los .py porque dashboard/forms.py
  // define clases en los widgets de Django (ver 'class' en attrs).
  content: [
    './dashboard/templates/**/*.html',
    './formularios/templates/**/*.html',
    './core/*.py',
    './dashboard/*.py',
    './empresas/*.py',
    './formularios/*.py',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      colors: {
        gfr: '#0a2342',
      },
    },
  },
  plugins: [],
}
