import type { Puzzle } from "./types";
import type { DayState } from "./storage";
import { GAME_NAME } from "./config";
import { formatTime } from "./date";

/**
 * Spoiler-free share text: the formation drawn as rows (attack at the top).
 * ⬛ pre-placed · 🟩 right first time · 🟨 needed more than one try
 */
export function shareText(p: Puzzle, s: DayState): string {
  // Group slots into lines of the formation (attack first): a new line starts when y drops by > 9.
  const bySlotY = [...p.formation.slots].sort((a, b) => b.y - a.y);
  const rows: (typeof bySlotY)[] = [];
  for (const slot of bySlotY) {
    const row = rows[rows.length - 1];
    if (row && row[0].y - slot.y <= 9) row.push(slot);
    else rows.push([slot]);
  }
  const lines = rows.map((row) =>
    row
      .sort((a, b) => a.x - b.x)
      .map(({ id }) => (p.seeds[id] ? "⬛" : (s.attempts[id] ?? 1) > 1 ? "🟨" : "🟩"))
      .join(""),
  );
  const d = new Date(`${p.date}T12:00:00Z`).toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
  const slips = s.mistakes === 0 ? "no wrong links" : `${s.mistakes} wrong link${s.mistakes === 1 ? "" : "s"}`;
  return [`${GAME_NAME} · ${d} · ${p.difficulty.label} · ${p.formation.name}`, ...lines, `✅ ${formatTime(s.elapsed)} · ${slips}`].join("\n");
}
