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
        // Decorative "notebook sketch" marks only — never used on clickable
        // elements. moss keeps sole ownership of anything interactive.
        navy: '#33415C',
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
        // Distinct from slideUp (the shell's one-time page-entry animation) —
        // this is the vision page's scroll-triggered, one-shot section reveal.
        revealUp: {
          '0%': { transform: 'translateY(12px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      animation: {
        slideUp: 'slideUp 300ms ease-out',
        revealUp: 'revealUp 400ms ease-out',
      },
    },
  },
  plugins: [],
}
