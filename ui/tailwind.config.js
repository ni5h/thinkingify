/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{html,ts}'],
  theme: {
    extend: {
      // Class 4 pilot palette (2026-10-10). Token NAMES are unchanged so the
      // existing components need no edits; only values changed. All
      // text-on-color pairs verified to meet WCAG AA (4.5:1; 3:1 for ≥24px).
      colors: {
        ink: '#16213B',
        paper: '#EDF1F5',
        cloud: '#D5DCE6',
        // Lighter divider/bar tint than cloud.
        'cloud-soft': '#E3E8EF',
        moss: '#14746F',
        'moss-dark': '#0E5652',
        // "Crack it" accent — light, only legible on dark (ink/navy) surfaces.
        amber: '#F5C26B',
        muted: '#56627A',
        navy: '#16213B',
        // Per-room tones + tints. room-sherlock darkened from the brief's
        // #A8650F to #94590C so its label text passes AA on its own tint.
        'room-ramanujan': '#14746F',
        'room-ramanujan-tint': '#DDF1EE',
        'room-einstein': '#2F5DA8',
        'room-einstein-tint': '#E1EBF9',
        'room-rowling': '#7B3F86',
        'room-rowling-tint': '#F0E3F3',
        'room-sherlock': '#94590C',
        'room-sherlock-tint': '#FBEBD0',
      },
      fontFamily: {
        display: ['Bricolage Grotesque', 'sans-serif'],
        sans: ['DM Sans', 'sans-serif'],
        mono: ['DM Mono', 'monospace'],
      },
      // Friendlier corners: cards (rounded-2xl) ~22px, buttons/inputs
      // (rounded-xl) 14px, small controls (rounded-lg) 12px. Names unchanged
      // so components are untouched. The old `sm: 2px` override is dropped.
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
