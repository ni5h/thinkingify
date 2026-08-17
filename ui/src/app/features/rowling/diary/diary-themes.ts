// Selectable visual skins for the diary page. Config-as-code, mirroring the
// STYLE_SCAFFOLDS precedent. Values are concrete CSS (not Tailwind classes) so
// they can be applied via inline [style] bindings — arbitrary per-theme colors
// wouldn't survive Tailwind's purge as dynamic class strings.

export type DiaryThemeKey = 'classic' | 'lined' | 'midnight' | 'sunny' | 'ocean';

export interface DiaryTheme {
  value: DiaryThemeKey;
  label: string;
  description: string;
  /** Page background — a solid colour, or a repeating gradient for ruled paper. */
  background: string;
  /** Body text colour. */
  ink: string;
  /** Accent used for the date header, buttons, rules. */
  accent: string;
  /** Muted text (meta, placeholders). */
  muted: string;
  /** Font stack for the writing surface. */
  fontFamily: string;
  /** A small swatch colour for the theme picker / entry cards. */
  swatch: string;
}

const SERIF = "'Fraunces', Georgia, serif";
const SANS = "'DM Sans', system-ui, sans-serif";
const HAND = "'Caveat', 'DM Sans', cursive";

// A subtle ruled-paper look built from a repeating linear gradient.
function ruledPaper(paper: string, line: string): string {
  return `repeating-linear-gradient(${paper}, ${paper} 31px, ${line} 31px, ${line} 32px)`;
}

export const DIARY_THEMES: Record<DiaryThemeKey, DiaryTheme> = {
  classic: {
    value: 'classic',
    label: 'Classic',
    description: 'Warm cream paper, storybook serif.',
    background: '#FBF6EC',
    ink: '#3B2E22',
    accent: '#9A6B3F',
    muted: '#8A7A67',
    fontFamily: SERIF,
    swatch: '#E4C99B',
  },
  lined: {
    value: 'lined',
    label: 'Lined notebook',
    description: 'Ruled pages and friendly handwriting.',
    background: ruledPaper('#FFFFFF', '#DCE7F2'),
    ink: '#1D2A3A',
    accent: '#2E5A8A',
    muted: '#6B7A8C',
    fontFamily: HAND,
    swatch: '#BFD6EC',
  },
  midnight: {
    value: 'midnight',
    label: 'Midnight',
    description: 'Cosy dark pages for evening writing.',
    background: '#1E293B',
    ink: '#E7E5E4',
    accent: '#F59E0B',
    muted: '#94A3B8',
    fontFamily: SERIF,
    swatch: '#334155',
  },
  sunny: {
    value: 'sunny',
    label: 'Sunny',
    description: 'Bright and cheerful, like a good day.',
    background: '#FEF6E3',
    ink: '#4A3B14',
    accent: '#D97706',
    muted: '#A08a5b',
    fontFamily: SANS,
    swatch: '#FBD38D',
  },
  ocean: {
    value: 'ocean',
    label: 'Ocean',
    description: 'Calm cool blues and clear water.',
    background: '#ECF6FB',
    ink: '#123141',
    accent: '#0E7490',
    muted: '#5A7A88',
    fontFamily: SANS,
    swatch: '#A9DCEC',
  },
};

export const DEFAULT_DIARY_THEME: DiaryThemeKey = 'classic';

export function resolveDiaryTheme(key: string | null | undefined): DiaryTheme {
  return DIARY_THEMES[(key as DiaryThemeKey)] ?? DIARY_THEMES[DEFAULT_DIARY_THEME];
}

export const DIARY_THEME_LIST: DiaryTheme[] = Object.values(DIARY_THEMES);
