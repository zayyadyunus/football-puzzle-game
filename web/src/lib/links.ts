import type { LinkVia, PlayerCard, Slot, Spell } from "./types";

/** Years (~3 weeks). Spells that merely touch at a transfer window don't count. Matches pipeline/links.py. */
export const MIN_OVERLAP = 0.05;

export function sharedTeams(a: Spell[], b: Spell[]): LinkVia[] {
  const out: LinkVia[] = [];
  for (const [t1, name, nat, a1, b1] of a) {
    for (const [t2, , , a2, b2] of b) {
      if (t1 !== t2) continue;
      const lo = Math.max(a1, a2);
      const hi = Math.min(b1, b2);
      if (hi - lo > MIN_OVERLAP) out.push({ team: name, national: nat, from: lo, to: hi });
    }
  }
  return out.sort((x, y) => x.from - y.from);
}

export function fitsSlot(p: PlayerCard, slot: Slot): boolean {
  if (!p.pos.length) return slot.accepts.some((g) => g !== "GK"); // unknown position: any outfield slot
  return p.pos.some((g) => slot.accepts.includes(g));
}

/** "England men's national association football team" → "England" */
export function teamLabel(name: string, national: boolean): string {
  return national ? name.replace(/\s+(men's\s+)?national\b.*$/i, "") : name;
}

/** "2004–2006", or "1995" for a single season; open-ended if `ongoing`. */
export function yearSpan(from: number, to: number, ongoing = false): string {
  const a = Math.floor(from);
  const b = Math.floor(to);
  if (ongoing) return `${a}–`;
  return a === b ? `${a}` : `${a}–${b}`;
}

export function formatVia(v: LinkVia): string {
  return `${teamLabel(v.team, v.national)}${v.national ? " (national team)" : ""} · ${yearSpan(v.from, v.to)}`;
}

const PARTICLES = new Set(["da", "de", "di", "do", "dos", "das", "del", "della", "van", "von", "der", "den", "le", "la", "du", "el", "al", "ter", "ten", "mac", "st."]);

/** Short display name for a shirt label: full name if short, else surname (keeping particles like "van"). */
export function shortName(name: string): string {
  const clean = name.replace(/\s*\(.*\)$/, "");
  if (clean.length <= 11) return clean;
  const parts = clean.split(" ");
  let i = parts.length - 1;
  while (i > 0 && PARTICLES.has(parts[i - 1].toLowerCase())) i--;
  return parts.slice(i).join(" ");
}
