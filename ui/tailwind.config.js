/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{html,ts}'],
  theme: {
    extend: {
      colors: {
        ink: '#1C1917',
        paper: '#FAFAF7',
        cloud: '#F0EFE9',
        moss: '#4A7C59',
        'moss-dark': '#2E5238',
        amber: '#D97706',
        muted: '#78716C',
      },
      fontFamily: {
        display: ['Fraunces', 'serif'],
        sans: ['DM Sans', 'sans-serif'],
        mono: ['DM Mono', 'monospace'],
      },
      borderRadius: {
        sm: '2px',
      },
      keyframes: {
        slideUp: {
          '0%': { transform: 'translateY(8px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      animation: {
        slideUp: 'slideUp 300ms ease-out',
      },
    },
  },
  plugins: [],
}
