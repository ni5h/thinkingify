function mirrorCase(matched: string, replacement: string): string {
  if (matched === matched.toUpperCase() && matched !== matched.toLowerCase()) {
    return replacement.toUpperCase();
  }
  if (matched[0] && matched[0] === matched[0].toUpperCase() && matched[0] !== matched[0].toLowerCase()) {
    return replacement.charAt(0).toUpperCase() + replacement.slice(1);
  }
  return replacement;
}

/**
 * Word-boundary-anchored, case-insensitive find-and-replace across every
 * occurrence of `oldWord` in `markdown`, mirroring each match's own
 * capitalization onto the replacement (so a sentence-initial correction
 * still reads "Here home", not "here home"). Returns null if `oldWord`
 * isn't present at all, so callers can skip a needless editor reset.
 *
 * Used from both the Rowling Writing Studio (per-section) and the Studio
 * post editor (single editor) — one shared implementation instead of
 * duplicating this regex logic in each.
 */
export function applyWordCorrection(markdown: string, oldWord: string, newWord: string): string | null {
  const escaped = oldWord.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const pattern = new RegExp(`\\b${escaped}\\b`, 'gi');
  let found = false;
  const replaced = markdown.replace(pattern, (match) => {
    found = true;
    return mirrorCase(match, newWord);
  });
  return found ? replaced : null;
}
