export interface ThemeDefinition {
  slug: string;
  label: string;
}

export const TOPIC_THEMES: ThemeDefinition[] = [
  { slug: 'sports', label: 'Sports' },
  { slug: 'science', label: 'Science' },
  { slug: 'physics', label: 'Physics' },
  { slug: 'chemistry', label: 'Chemistry' },
  { slug: 'biology', label: 'Biology' },
  { slug: 'human-body', label: 'Human Body' },
  { slug: 'animals', label: 'Animals' },
  { slug: 'space', label: 'Space' },
  { slug: 'history', label: 'History' },
  { slug: 'geography', label: 'Geography' },
  { slug: 'technology', label: 'Technology' },
  { slug: 'art-and-music', label: 'Art & Music' },
  { slug: 'myths-and-legends', label: 'Myths & Legends' },
  { slug: 'how-things-work', label: 'How Things Work' },
];

// Backend never validates Topic.themes contents (same "plain string, no
// DB enum" philosophy as Content.style) — a slug in the DB but absent
// here must still render, so callers do TOPIC_THEME_LABELS[slug] ?? slug.
export const TOPIC_THEME_LABELS: Record<string, string> = Object.fromEntries(
  TOPIC_THEMES.map((t) => [t.slug, t.label])
);
