/**
 * Literal find-and-replace of one full sentence with its rewritten
 * version, across every occurrence in `markdown`. Unlike
 * apply-word-correction's word-boundary regex, a full sentence is
 * specific enough that a plain literal match is safe — no
 * regex-escaping or case-mirroring needed. Returns null if `oldSentence`
 * isn't present, so callers can skip a needless editor reset.
 *
 * Used from both the Rowling Writing Studio (per-section) and the Studio
 * post editor (single editor), mirroring apply-word-correction's role in
 * the Spelling gate.
 */
export function applySentenceCorrection(markdown: string, oldSentence: string, newSentence: string): string | null {
  if (!markdown.includes(oldSentence)) return null;
  return markdown.split(oldSentence).join(newSentence);
}
