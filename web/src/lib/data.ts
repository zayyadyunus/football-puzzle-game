import type { PlayerCard, PosGroup, Puzzle, Spell } from "./types";

const SHARDS = 512; // keep in sync with pipeline/export_web.py
const base = "/data";

const jsonCache = new Map<string, Promise<unknown>>();

function getJSON<T>(url: string): Promise<T> {
  let p = jsonCache.get(url);
  if (!p) {
    p = fetch(url).then((r) => {
      if (!r.ok) throw new Error(`${r.status} ${url}`);
      return r.json();
    });
    p.catch(() => jsonCache.delete(url)); // allow retry after a failure
    jsonCache.set(url, p);
  }
  return p as Promise<T>;
}

// ---------------------------------------------------------------- puzzles

export function loadPuzzleIndex() {
  return getJSON<{ dates: string[] }>(`${base}/puzzles/index.json`);
}

export function loadPuzzle(date: string) {
  return getJSON<Puzzle>(`${base}/puzzles/${date}.json`);
}

// ---------------------------------------------------------------- careers

export async function loadCareer(pid: string): Promise<Spell[]> {
  const shard = Number(pid.slice(1)) % SHARDS;
  const players = await getJSON<Record<string, Spell[]>>(`${base}/p/${shard}.json`);
  return players[pid] ?? [];
}

// ---------------------------------------------------------------- search

/** Must match pipeline/export_web.py norm()/tokens(). */
export function normalise(s: string): string {
  return s
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/ø/g, "o")
    .replace(/Ø/g, "O")
    .replace(/ł/g, "l")
    .replace(/Ł/g, "L")
    .replace(/đ/g, "d")
    .replace(/ß/g, "ss")
    .toLowerCase();
}

export function tokens(s: string): string[] {
  return normalise(s)
    .split(/[^a-z0-9]+/)
    .filter((t) => t.length >= 1);
}

/** Row format from export_web.py: [id, name, nat, "DEF/MID", born, careerStart, careerEnd, fame] */
type SearchRow = [string, string, string, string, number, number, number, number];

export interface SearchResult extends PlayerCard {
  fame: number;
}

function toCard(r: SearchRow): SearchResult {
  return {
    id: r[0],
    name: r[1],
    nat: r[2] || null,
    pos: (r[3] ? r[3].split("/") : []) as PosGroup[],
    born: r[4] || null,
    career: r[5] ? [r[5], r[6]] : null,
    fame: r[7],
  };
}

export async function searchPlayers(query: string, limit = 25): Promise<SearchResult[]> {
  const qt = tokens(query).filter((t) => t.length >= 2);
  if (!qt.length) return [];
  // The longest token picks the index file: its 3-char prefix, or the whole word if it's 2 letters
  // (2-letter name words like "Zé" have their own file).
  const key = [...qt].sort((a, b) => b.length - a.length)[0];
  const file = key.slice(0, 3);
  let rows: SearchRow[];
  try {
    rows = await getJSON<SearchRow[]>(`${base}/search/${file}.json`);
  } catch {
    return [];
  }
  const out: SearchResult[] = [];
  for (const r of rows) {
    const nt = tokens(r[1]);
    // every query token must prefix-match a distinct-enough name token
    if (qt.every((q) => nt.some((t) => t.startsWith(q)))) {
      out.push(toCard(r));
      if (out.length >= limit) break;
    }
  }
  return out; // rows are pre-sorted by fame
}
