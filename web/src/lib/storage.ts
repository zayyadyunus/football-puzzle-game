import type { PlayerCard } from "./types";
import { addDays } from "./date";

const PREFIX = "xi:v1:";

export interface DayState {
  placed: Record<string, PlayerCard>; // slot id → player (user-placed only)
  attempts: Record<string, number>; // slot id → number of placements made there
  mistakes: number; // placements that created at least one invalid link
  elapsed: number; // active seconds
  started: boolean; // timer runs once the player first opens a slot
  completed: boolean;
}

export const emptyDay = (): DayState => ({ placed: {}, attempts: {}, mistakes: 0, elapsed: 0, started: false, completed: false });

function read<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(PREFIX + key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

function write(key: string, value: unknown) {
  try {
    localStorage.setItem(PREFIX + key, JSON.stringify(value));
  } catch {
    /* storage unavailable (private mode etc.) — the game still works for this session */
  }
}

export const loadDay = (date: string) => read<DayState>(`day:${date}`);
export const saveDay = (date: string, s: DayState) => write(`day:${date}`, s);

export interface HistoryEntry {
  time: number;
  mistakes: number;
}
export const loadHistory = () => read<Record<string, HistoryEntry>>("history") ?? {};
export function recordWin(date: string, entry: HistoryEntry) {
  const h = loadHistory();
  if (!h[date]) {
    h[date] = entry;
    write("history", h);
  }
}

export const hasSeenHelp = () => read<boolean>("seen-help") ?? false;
export const markHelpSeen = () => write("seen-help", true);

export interface Stats {
  completed: number;
  currentStreak: number;
  maxStreak: number;
  avgTime: number | null;
  perfect: number; // completed with no mistakes
}

/** Streaks count consecutive puzzle days completed, ending today or yesterday. */
export function computeStats(today: string): Stats {
  const h = loadHistory();
  const dates = Object.keys(h).sort();
  let maxStreak = 0;
  let run = 0;
  let prev: string | null = null;
  for (const d of dates) {
    run = prev && addDays(prev, 1) === d ? run + 1 : 1;
    maxStreak = Math.max(maxStreak, run);
    prev = d;
  }
  let currentStreak = 0;
  let cursor = h[today] ? today : addDays(today, -1);
  while (h[cursor]) {
    currentStreak++;
    cursor = addDays(cursor, -1);
  }
  const times = dates.map((d) => h[d].time);
  return {
    completed: dates.length,
    currentStreak,
    maxStreak,
    avgTime: times.length ? times.reduce((a, b) => a + b, 0) / times.length : null,
    perfect: dates.filter((d) => h[d].mistakes === 0).length,
  };
}
