/**
 * Decide which paragraphs of a page belong to a cited snippet. Both sides are compared
 * after collapsing whitespace, because extraction and chunking space text differently.
 */

const PROBE_CHARS = 40;

export function normalize(text: string): string {
  return text.replace(/\s+/g, " ").replace(/…$/, "").trim().toLowerCase();
}

export function isHighlighted(paragraph: string, snippet: string): boolean {
  const p = normalize(paragraph);
  const s = normalize(snippet);
  if (!p || !s) return false;
  // The paragraph sits inside the snippet, or the snippet starts inside the paragraph.
  return (
    s.includes(p.slice(0, PROBE_CHARS)) || p.includes(s.slice(0, PROBE_CHARS))
  );
}
