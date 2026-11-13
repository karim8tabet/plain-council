// "What changed": compares the official text of one step with the next, word by word.
// Code only, no AI. The texts are numbered parts ("1. City Council increase…"), so parts are
// matched first (they can be renumbered when parts are added), then words inside each part.
// It shows wording, not meaning; the card says so and links the official record.

export type Part = { n: number; text: string };
export type Seg = { op: "same" | "add" | "del"; text: string };
export type PartChange =
  | { kind: "same"; newN: number; oldN: number }
  | { kind: "changed"; newN: number; oldN: number; segs: Seg[] }
  | { kind: "added"; newN: number; text: string }
  | { kind: "removed"; oldN: number; text: string };

/** Split "… recommends that: 1. … 2. …" into its numbered parts, in order.
 *  A number only starts a part if it is the next expected one and is followed by a capital,
 *  so "Section 71-11.1C" or "Fee Ref. 61.06" never split a part. */
export function splitParts(text: string): Part[] {
  const parts: Part[] = [];
  let n = 1;
  let start = -1;
  const re = /(^|\s)(\d{1,2})\.\s+(?=[A-Z])/g;
  for (let m = re.exec(text); m; m = re.exec(text)) {
    if (Number(m[2]) !== n) continue;
    const at = m.index + m[1].length;
    if (start >= 0) parts.push({ n: n - 1, text: text.slice(start, at).trim() });
    start = at + m[0].length - m[1].length;
    n += 1;
  }
  if (start >= 0) parts.push({ n: n - 1, text: text.slice(start).trim() });
  return parts;
}

// A word (or a "/") together with the spaces after it, so the original text is kept exactly.
type Tok = { key: string; raw: string };
function tokens(s: string): Tok[] {
  return [...s.matchAll(/(\/|[^\s/]+)(\s*)/g)].map((m) => ({
    raw: m[0],
    key: m[1].replace(/[‘’]/g, "'").replace(/[“”]/g, '"'),
  }));
}

function lcsTable(a: Tok[], b: Tok[]): number[][] {
  const t = Array.from({ length: a.length + 1 }, () => new Array<number>(b.length + 1).fill(0));
  for (let i = a.length - 1; i >= 0; i--)
    for (let j = b.length - 1; j >= 0; j--)
      t[i][j] = a[i].key === b[j].key ? t[i + 1][j + 1] + 1 : Math.max(t[i + 1][j], t[i][j + 1]);
  return t;
}

/** How alike two parts are, 0..1 (shared words in order). */
export function similarity(a: string, b: string): number {
  const ta = tokens(a), tb = tokens(b);
  if (!ta.length && !tb.length) return 1;
  return (2 * lcsTable(ta, tb)[0][0]) / (ta.length + tb.length);
}

/** Word-level differences between two versions of a part. */
export function wordDiff(oldText: string, newText: string): Seg[] {
  const a = tokens(oldText), b = tokens(newText), t = lcsTable(a, b);
  const segs: Seg[] = [];
  const push = (op: Seg["op"], raw: string) => {
    const last = segs[segs.length - 1];
    if (last && last.op === op) last.text += raw;
    else segs.push({ op, text: raw });
  };
  let i = 0, j = 0;
  while (i < a.length || j < b.length) {
    if (i < a.length && j < b.length && a[i].key === b[j].key) { push("same", b[j].raw); i++; j++; }
    // Removed words come before the words that replace them ("HST" then "Harmonized Sales Tax").
    else if (i < a.length && (j === b.length || t[i + 1][j] >= t[i][j + 1])) { push("del", a[i].raw); i++; }
    else { push("add", b[j].raw); j++; }
  }
  return segs;
}

const MATCH = 0.5; // parts sharing less than half their words are treated as different parts

/** Compare two steps' texts part by part. Result is in the newer step's order, then removed parts. */
export function compareSteps(oldText: string, newText: string): PartChange[] {
  const olds = splitParts(oldText), news = splitParts(newText);
  const used = new Set<number>();
  const out: PartChange[] = [];
  for (const p of news) {
    let best = -1, bestSim = MATCH;
    olds.forEach((o, k) => {
      if (used.has(k)) return;
      const s = similarity(o.text, p.text);
      if (s >= bestSim) { best = k; bestSim = s; }
    });
    if (best < 0) { out.push({ kind: "added", newN: p.n, text: p.text }); continue; }
    used.add(best);
    const o = olds[best];
    const segs = wordDiff(o.text, p.text);
    out.push(segs.every((s) => s.op === "same")
      ? { kind: "same", newN: p.n, oldN: o.n }
      : { kind: "changed", newN: p.n, oldN: o.n, segs });
  }
  olds.forEach((o, k) => { if (!used.has(k)) out.push({ kind: "removed", oldN: o.n, text: o.text }); });
  return out;
}
