"use client";

import { useEffect, useState } from "react";
import Sheet from "./Sheet";
import { shareText } from "@/lib/share";
import { formatTime, msUntilNextPuzzle } from "@/lib/date";
import type { Stats, DayState } from "@/lib/storage";
import type { Puzzle } from "@/lib/types";

interface Props {
  puzzle: Puzzle;
  day: DayState;
  stats: Stats | null; // null when playing an archive puzzle
  onClose: () => void;
}

function Countdown() {
  const [ms, setMs] = useState<number | null>(null);
  useEffect(() => {
    const tick = () => setMs(msUntilNextPuzzle());
    tick();
    const t = setInterval(tick, 1000);
    return () => clearInterval(t);
  }, []);
  if (ms === null) return null;
  const s = Math.floor(ms / 1000);
  const hh = String(Math.floor(s / 3600)).padStart(2, "0");
  const mm = String(Math.floor((s % 3600) / 60)).padStart(2, "0");
  const ss = String(s % 60).padStart(2, "0");
  return <span className="font-serif text-2xl font-semibold tabular-nums">{`${hh}:${mm}:${ss}`}</span>;
}

export default function ResultSheet({ puzzle, day, stats, onClose }: Props) {
  const [copied, setCopied] = useState(false);
  const [showRef, setShowRef] = useState(false);
  const text = shareText(puzzle, day);

  async function share() {
    try {
      if (navigator.share && matchMedia("(pointer: coarse)").matches) {
        await navigator.share({ text });
        return;
      }
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* user cancelled the share sheet */
    }
  }

  const tiles: [string, string][] = stats
    ? [
        [String(stats.completed), "Solved"],
        [String(stats.currentStreak), "Streak"],
        [String(stats.maxStreak), "Best streak"],
        [String(stats.perfect), "Perfect"],
      ]
    : [];

  return (
    <Sheet title="Full time!" subtitle={`${puzzle.difficulty.label} · ${puzzle.formation.name}`} onClose={onClose}>
      <div className="space-y-6 px-5 py-5">
        <div className="grid grid-cols-2 gap-3 text-center">
          <div className="rounded-xl bg-bg py-3">
            <div className="font-serif text-3xl font-semibold tabular-nums">{formatTime(day.elapsed)}</div>
            <div className="text-xs uppercase tracking-wider text-muted">Time</div>
          </div>
          <div className="rounded-xl bg-bg py-3">
            <div className="font-serif text-3xl font-semibold tabular-nums">{day.mistakes}</div>
            <div className="text-xs uppercase tracking-wider text-muted">Wrong links</div>
          </div>
        </div>

        <pre className="whitespace-pre rounded-xl border border-line px-4 py-3 text-center font-sans text-sm leading-6">{text}</pre>

        <button onClick={share} className="w-full rounded-full bg-accent py-3.5 font-semibold text-accent-ink">
          {copied ? "Copied to clipboard" : "Share result"}
        </button>

        {stats && (
          <div className="grid grid-cols-4 gap-2 text-center">
            {tiles.map(([v, l]) => (
              <div key={l}>
                <div className="font-serif text-2xl font-semibold">{v}</div>
                <div className="text-[11px] leading-tight text-muted">{l}</div>
              </div>
            ))}
          </div>
        )}

        <div className="flex items-center justify-between border-t border-line pt-4">
          <span className="text-sm text-muted">Next puzzle in</span>
          <Countdown />
        </div>

        <div className="border-t border-line pt-4">
          <button onClick={() => setShowRef((v) => !v)} className="text-sm font-semibold underline underline-offset-4" aria-expanded={showRef}>
            {showRef ? "Hide" : "Show"} the setter&apos;s XI
          </button>
          {showRef && (
            <ul className="mt-3 space-y-1 text-sm">
              {puzzle.formation.slots.map((s) => (
                <li key={s.id} className="flex justify-between gap-3">
                  <span className="w-10 shrink-0 text-muted">{s.label}</span>
                  <span className="flex-1 truncate">
                    {puzzle.solution[s.id].name}
                    {puzzle.seeds[s.id] && <span className="text-muted"> (given)</span>}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </Sheet>
  );
}
