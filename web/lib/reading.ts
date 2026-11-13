// Flesch-Kincaid grade level of the PUBLISHED sentences, computed when the card is shown,
// so it always matches what residents actually read. Same formula the pipeline uses
// (textstat). Syllables are estimated from vowel groups, so it is approximate; checked
// against textstat on sample sentences (within about 1 grade).
function syllables(word: string): number {
  const w = word.toLowerCase().replace(/[^a-z]/g, "");
  if (!w) return 1; // numbers and symbols count as one
  const trimmed = w.replace(/(?:[^laeiouy]es|[^laeiouy]ed|[^laeiouy]e)$/, "").replace(/^y/, "");
  const groups = trimmed.match(/[aeiouy]+/g)?.length ?? 0;
  const splits = trimmed.match(/ia|io|eo|ua|uo|iu/g)?.length ?? 0; // two sounds: pe-des-tri-ans
  return Math.max(1, groups + splits);
}

export function readingGrade(sentences: string[]): number | null {
  const words = sentences.join(" ").split(/\s+/).filter((w) => /[a-z0-9]/i.test(w));
  const count = sentences.join(" ").split(/[.!?]+(?:\s|$)/).filter((s) => s.trim()).length;
  if (count === 0 || words.length === 0) return null;
  const syl = words.reduce((n, w) => n + syllables(w), 0);
  return 0.39 * (words.length / count) + 11.8 * (syl / words.length) - 15.59;
}
