/** @type {import('tailwindcss').Config} */
// Same design tokens as the main Thinkingify app, so Neo's product looks and
// feels like part of the family. Change these to make the book community
// its own thing — that's a real product-design decision.
module.exports = {
  content: ['./src/**/*.{html,ts}'],
  theme: {
    extend: {
      colors: {
        ink: '#16213B',
        paper: '#EDF1F5',
        cloud: '#D5DCE6',
        'cloud-soft': '#E3E8EF',
        moss: '#14746F',
        'moss-dark': '#0E5652',
        amber: '#F5C26B',
        muted: '#56627A',
        navy: '#16213B',
        // The book community's own accent — a warm book-spine coral.
        spine: '#E8743B',
        'spine-tint': '#FBE6DB',
      },
      fontFamily: {
        display: ['Bricolage Grotesque', 'sans-serif'],
        sans: ['DM Sans', 'sans-serif'],
        mono: ['DM Mono', 'monospace'],
        hand: ['Caveat', 'cursive'],
      },
      borderRadius: {
        lg: '0.75rem',
        xl: '0.875rem',
        '2xl': '1.375rem',
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
};
