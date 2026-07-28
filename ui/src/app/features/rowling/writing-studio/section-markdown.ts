import { WritingStyle } from '../../../core/models/content';
import { STYLE_SCAFFOLDS, ScaffoldSection, StyleScaffold } from './style-scaffolds';

export interface ParsedSections {
  content: Record<string, string>;
  foundIndices: number[];
}

export type EditorMode =
  | { mode: 'blank'; seed: string }
  | { mode: 'scaffolded'; scaffold: StyleScaffold; content: Record<string, string>; revealedCount: number };

function splitOnHeadings(markdown: string): { heading: string; body: string }[] {
  const lines = markdown.split('\n');
  const chunks: { heading: string; body: string[] }[] = [];
  let current: { heading: string; body: string[] } | null = null;

  for (const line of lines) {
    const match = /^## (.+)$/.exec(line);
    if (match) {
      if (current) chunks.push(current);
      current = { heading: match[1], body: [] };
    } else if (current) {
      current.body.push(line);
    }
  }
  if (current) chunks.push(current);

  return chunks.map((c) => ({ heading: c.heading, body: c.body.join('\n') }));
}

/** Splits saved markdown back into per-section content, matched against a
 *  style's known ordered headings. `foundIndices` is which of `sections`
 *  (by array position) had a matching heading present in the markdown. */
export function parseSectionMarkdown(markdown: string, sections: ScaffoldSection[]): ParsedSections {
  const chunks = splitOnHeadings(markdown);
  const content: Record<string, string> = {};
  const foundIndices: number[] = [];

  sections.forEach((section, index) => {
    const match = chunks.find((c) => c.heading.trim() === section.id);
    content[section.id] = match ? match.body.trim() : '';
    if (match) foundIndices.push(index);
  });

  return { content, foundIndices };
}

/** Inverse of parseSectionMarkdown — only revealed sections are written
 *  out, in order, producing the same heading-then-prose shape the app has
 *  always published. */
export function assembleSectionMarkdown(
  sections: ScaffoldSection[],
  content: Record<string, string>,
  revealedCount: number
): string {
  return sections
    .slice(0, revealedCount)
    .map((section) => `## ${section.id}\n\n${(content[section.id] ?? '').trim()}\n\n`)
    .join('');
}

/** The single fallback point for resuming a draft. Unrecognized/legacy
 *  styles, or content that doesn't match any of a recognized style's
 *  expected headings at all, fall back to plain 'blank' mode seeded with
 *  the raw markdown verbatim — never discards content, never throws. */
export function resolveEditorMode(style: string | null, markdown: string): EditorMode {
  const scaffold = style ? STYLE_SCAFFOLDS[style as WritingStyle] : undefined;

  if (!scaffold || scaffold.sections === null) {
    return { mode: 'blank', seed: markdown };
  }

  const { content, foundIndices } = parseSectionMarkdown(markdown, scaffold.sections);

  if (foundIndices.length === 0 && markdown.trim() !== '') {
    return { mode: 'blank', seed: markdown };
  }

  const revealedCount =
    foundIndices.length === 0 ? 1 : Math.min(Math.max(...foundIndices) + 2, scaffold.sections.length);

  return { mode: 'scaffolded', scaffold, content, revealedCount };
}
