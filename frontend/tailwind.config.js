/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        rr: {
          pink: '#E6007E',
          deep: '#B90063',
          deepPink: '#B90063',
          soft: '#FCE7F2',
          softPink: '#FCE7F2',
          pale: '#FFF5FA',
          palePink: '#FFF5FA',
          white: '#FFFFFF',
          warm: '#FFFBFD',
          warmWhite: '#FFFBFD',
          charcoal: '#25212A',
          muted: '#77717C',
          border: '#F0E7ED',
          blue: '#4776A8',
          rare: '#4776A8',
          navy: '#0B192C',
          navyLight: '#1B2A4A',
          darkNavy: '#051026',
          gold: '#D4AF37',
          light: '#F8FAFC',
        }
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
        heading: ['Plus Jakarta Sans', 'Outfit', 'sans-serif'],
        display: ['Syne', 'Plus Jakarta Sans', 'sans-serif'],
        royal: ['Cinzel', 'Georgia', 'serif'],
        cursive: ['Great Vibes', 'Alex Brush', 'Allura', 'Parisienne', 'Pinyon Script', 'cursive'],
        italicDisplay: ['Playfair Display', 'Georgia', 'serif'],
      },
      boxShadow: {
        'subtle': '0 1px 3px rgba(37, 33, 42, 0.05), 0 1px 2px rgba(230, 0, 126, 0.02)',
        'card': '0 4px 12px rgba(37, 33, 42, 0.04), 0 1px 3px rgba(230, 0, 126, 0.03)',
        'hover': '0 8px 24px rgba(230, 0, 126, 0.08), 0 2px 6px rgba(37, 33, 42, 0.04)',
        'rr-subtle': '0 1px 3px rgba(37, 33, 42, 0.05), 0 1px 2px rgba(230, 0, 126, 0.02)',
        'rr-card': '0 4px 12px rgba(37, 33, 42, 0.04), 0 1px 3px rgba(230, 0, 126, 0.03)',
        'rr-hover': '0 8px 24px rgba(230, 0, 126, 0.08), 0 2px 6px rgba(37, 33, 42, 0.04)',
      }
    },
  },
  plugins: [],
}
