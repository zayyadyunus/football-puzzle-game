"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Pitch, { type SlotView } from "./Pitch";
import SearchSheet from "./SearchSheet";
import PlayerSheet from "./PlayerSheet";
import HelpSheet from "./HelpSheet";
import ResultSheet from "./ResultSheet";
import { loadCareer, loadPuzzle, loadPuzzleIndex } from "@/lib/data";
import { sharedTeams } from "@/lib/links";
import { formatTime, prettyDate, todayUK } from "@/lib/date";
import { computeStats, emptyDay, hasSeenHelp, loadDay, markHelpSeen, recordWin, saveDay, type DayState } from "@/lib/storage";
import { GAME_NAME } from "@/lib/config";
import type { LinkState, PlayerCard, Puzzle, Spell } from "@/lib/types";

type SheetState = { kind: "search"; slot: string } | { kind: "player"; slot: string } | { kind: "help" } | { kind: "result" } | null;

export default function Game() {
  const [today, setToday] = useState<string | null>(null);
  const [dates, setDates] = useState<string[]>([]);
  const [date, setDate] = useState<string | null>(null);
  const [puzzle, setPuzzle] = useState<Puzzle | null>(null);
  const [day, setDay] = useState<DayState>(emptyDay);
  const [careers, setCareers] = useState<Record<string, Spell[]>>({});
  const [sheet, setSheet] = useState<SheetState>(null);
  const [fresh, setFresh] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // ---------------------------------------------------------------- loading
  useEffect(() => {
    const t = todayUK();
    loadPuzzleIndex()
      .then(({ dates }) => {
        const requested = new URLSearchParams(window.location.search).get("date");
        const playable = dates.filter((d) => d <= t);
        const pick =
          (requested && dates.includes(requested) && requested) ||
          (dates.includes(t) && t) ||
          playable[playable.length - 1] ||
          dates[0];
        setToday(t);
        setDates(dates);
        setDate(pick ?? null);
        if (!pick) setError("No puzzles yet. Check back soon.");
        if (!hasSeenHelp()) {
          setSheet({ kind: "help" });
          markHelpSeen();
        }
      })
      .catch(() => setError("Couldn't load the puzzle. Check your connection and refresh."));
  }, []);

  const ensureCareers = useCallback((ids: string[]) => {
    ids.forEach((id) =>
      loadCareer(id)
        .then((c) => setCareers((prev) => (prev[id] ? prev : { ...prev, [id]: c })))
        .catch(() => {}),
    );
  }, []);

  useEffect(() => {
    if (!date) return;
    let cancelled = false;
    loadPuzzle(date)
      .then((p) => {
        if (cancelled) return;
        const saved = loadDay(date) ?? emptyDay();
        setPuzzle(p);
        setDay(saved);
        ensureCareers([...Object.values(p.seeds), ...Object.values(saved.placed)].map((c) => c.id));
      })
      .catch(() => !cancelled && setError("Couldn't load the puzzle. Check your connection and refresh."));
    return () => {
      cancelled = true;
    };
  }, [date, ensureCareers]);

  // ---------------------------------------------------------------- persistence + timer
  useEffect(() => {
    if (date && puzzle?.date === date) saveDay(date, day);
  }, [date, puzzle, day]);

  const running = !!puzzle && day.started && !day.completed;
  useEffect(() => {
    if (!running) return;
    const t = setInterval(() => {
      if (document.visibilityState === "visible") setDay((d) => ({ ...d, elapsed: d.elapsed + 1 }));
    }, 1000);
    return () => clearInterval(t);
  }, [running]);

  // ---------------------------------------------------------------- derived state
  const nbrs = useMemo(() => {
    const m: Record<string, string[]> = {};
    puzzle?.formation.links.forEach(([a, b]) => {
      (m[a] ??= []).push(b);
      (m[b] ??= []).push(a);
    });
    return m;
  }, [puzzle]);

  const playerAt = useCallback(
    (slot: string, placed = day.placed): PlayerCard | null => puzzle?.seeds[slot] ?? placed[slot] ?? null,
    [puzzle, day.placed],
  );

  const linkState = useCallback(
    (a: string, b: string, placed = day.placed, extra: Record<string, Spell[]> = {}): LinkState => {
      const pa = playerAt(a, placed);
      const pb = playerAt(b, placed);
      if (!pa || !pb) return "pending";
      const ca = extra[pa.id] ?? careers[pa.id];
      const cb = extra[pb.id] ?? careers[pb.id];
      if (!ca || !cb) return "pending";
      return sharedTeams(ca, cb).length ? "valid" : "invalid";
    },
    [playerAt, careers, day.placed],
  );

  const links = useMemo(
    () => (puzzle ? puzzle.formation.links.map(([a, b]) => ({ a, b, state: linkState(a, b) })) : []),
    [puzzle, linkState],
  );
  const validCount = links.filter((l) => l.state === "valid").length;

  const slotViews: SlotView[] = useMemo(
    () =>
      puzzle
        ? puzzle.formation.slots.map((slot) => ({
            slot,
            player: playerAt(slot.id),
            seed: !!puzzle.seeds[slot.id],
            hasInvalid: !puzzle.seeds[slot.id] && links.some((l) => (l.a === slot.id || l.b === slot.id) && l.state === "invalid"),
            fresh: fresh === slot.id,
          }))
        : [],
    [puzzle, playerAt, links, fresh],
  );

  // ---------------------------------------------------------------- actions
  async function place(slotId: string, card: PlayerCard) {
    if (!puzzle || !date) return;
    setSheet(null);
    let career: Spell[];
    try {
      career = await loadCareer(card.id);
    } catch {
      setError("Couldn't check that player. Try again.");
      return;
    }
    setCareers((prev) => ({ ...prev, [card.id]: career }));
    const placed = { ...day.placed, [slotId]: card };
    const extra = { [card.id]: career };
    const newInvalid = (nbrs[slotId] ?? []).some((n) => linkState(slotId, n, placed, extra) === "invalid");
    const allLinks = puzzle.formation.links.map(([a, b]) => linkState(a, b, placed, extra));
    const solved = puzzle.formation.slots.every((s) => playerAt(s.id, placed)) && allLinks.every((s) => s === "valid");

    const next: DayState = {
      ...day,
      placed,
      started: true,
      attempts: { ...day.attempts, [slotId]: (day.attempts[slotId] ?? 0) + 1 },
      mistakes: day.mistakes + (newInvalid ? 1 : 0),
      completed: solved,
    };
    setDay(next);
    setFresh(slotId);
    setTimeout(() => setFresh((f) => (f === slotId ? null : f)), 400);
    if (solved) {
      if (date === today) recordWin(date, { time: next.elapsed, mistakes: next.mistakes });
      setTimeout(() => setSheet({ kind: "result" }), 700);
    }
  }

  function remove(slotId: string) {
    setDay((d) => {
      const placed = { ...d.placed };
      delete placed[slotId];
      return { ...d, placed };
    });
    setSheet(null);
  }

  function openSlot(slotId: string) {
    if (!puzzle) return;
    if (playerAt(slotId)) {
      setSheet({ kind: "player", slot: slotId });
    } else if (!day.completed) {
      setDay((d) => (d.started ? d : { ...d, started: true }));
      setSheet({ kind: "search", slot: slotId });
    }
  }

  // ---------------------------------------------------------------- render
  const idx = date ? dates.indexOf(date) : -1;
  const prevDate = idx > 0 ? dates[idx - 1] : null;
  const nextDate = idx >= 0 && idx < dates.length - 1 && today && dates[idx + 1] <= today ? dates[idx + 1] : null;
  const go = (d: string) => {
    setPuzzle(null);
    setSheet(null);
    setDate(d);
    const url = new URL(window.location.href);
    if (d === today) url.searchParams.delete("date");
    else url.searchParams.set("date", d);
    window.history.replaceState(null, "", url);
  };

  const slotById = (id: string) => puzzle!.formation.slots.find((s) => s.id === id)!;

  return (
    <>
      <header className="flex items-center justify-between border-b border-line py-3">
        <h1 className="font-serif text-[28px] font-extrabold leading-none tracking-tight">{GAME_NAME}</h1>
        <div className="flex items-center gap-1">
          {day.completed && puzzle && (
            <button onClick={() => setSheet({ kind: "result" })} className="rounded-full px-3 py-1.5 text-sm font-semibold hover:bg-line/60">
              Results
            </button>
          )}
          <button
            onClick={() => setSheet({ kind: "help" })}
            className="flex h-9 w-9 items-center justify-center rounded-full border border-ink text-sm font-bold hover:bg-ink hover:text-bg"
            aria-label="How to play"
          >
            ?
          </button>
        </div>
      </header>

      {error && (
        <p role="alert" className="mt-4 rounded-xl border border-bad/40 bg-bad/10 px-4 py-3 text-sm">
          {error}{" "}
          <button className="font-semibold underline" onClick={() => setError(null)}>
            Dismiss
          </button>
        </p>
      )}

      {!puzzle && !error && (
        <div className="mt-5 animate-pulse" aria-busy>
          <div className="mb-4 h-5 w-48 rounded bg-line" />
          <div className="aspect-[4/5] w-full rounded-2xl bg-line" />
        </div>
      )}

      {puzzle && date && (
        <>
          <div className="flex items-center justify-between gap-2 py-3">
            <button
              onClick={() => prevDate && go(prevDate)}
              disabled={!prevDate}
              className="flex h-10 w-10 items-center justify-center rounded-full text-2xl leading-none text-muted hover:bg-line/60 disabled:opacity-25"
              aria-label="Previous puzzle"
            >
              ‹
            </button>
            <div className="text-center">
              <div className="font-semibold">
                {prettyDate(date)}
                {date !== today && <span className="ml-2 rounded-full bg-line px-2 py-0.5 text-xs font-semibold text-muted">Archive</span>}
              </div>
              <div className="text-sm text-muted">
                {puzzle.difficulty.label} · {puzzle.formation.name}
              </div>
            </div>
            <button
              onClick={() => nextDate && go(nextDate)}
              disabled={!nextDate}
              className="flex h-10 w-10 items-center justify-center rounded-full text-2xl leading-none text-muted hover:bg-line/60 disabled:opacity-25"
              aria-label="Next puzzle"
            >
              ›
            </button>
          </div>

          <Pitch formation={puzzle.formation} slots={slotViews} links={links} onSlot={openSlot} />

          <div className="mt-3 flex items-center justify-between text-sm">
            <span>
              <span className="font-semibold tabular-nums">
                {validCount}/{links.length}
              </span>{" "}
              <span className="text-muted">links</span>
              {day.mistakes > 0 && <span className="text-muted"> · {day.mistakes} wrong</span>}
            </span>
            <span className="font-semibold tabular-nums" aria-label={`Time ${formatTime(day.elapsed)}`}>
              {formatTime(day.elapsed)}
            </span>
          </div>

          {/* progress bar */}
          <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-line" aria-hidden>
            <div className="h-full rounded-full bg-good transition-[width] duration-300" style={{ width: `${(validCount / links.length) * 100}%` }} />
          </div>

          {day.completed ? (
            <button onClick={() => setSheet({ kind: "result" })} className="mt-5 w-full rounded-full bg-accent py-3.5 font-semibold text-accent-ink">
              Solved in {formatTime(day.elapsed)}. See results
            </button>
          ) : (
            <p className="mt-4 text-center text-sm text-muted">Tap an empty shirt to pick a player. Tap a player to see their links.</p>
          )}
        </>
      )}

      {sheet?.kind === "help" && <HelpSheet onClose={() => setSheet(null)} />}

      {puzzle && sheet?.kind === "search" && (
        <SearchSheet
          slot={slotById(sheet.slot)}
          neighbours={(nbrs[sheet.slot] ?? []).map((n) => playerAt(n)).filter((p): p is PlayerCard => !!p)}
          usedIds={new Set(puzzle.formation.slots.map((s) => playerAt(s.id)?.id).filter((x): x is string => !!x))}
          onPick={(p) => place(sheet.slot, p)}
          onClose={() => setSheet(null)}
        />
      )}

      {puzzle && sheet?.kind === "player" && playerAt(sheet.slot) && (
        <PlayerSheet
          slot={slotById(sheet.slot)}
          player={playerAt(sheet.slot)!}
          seed={!!puzzle.seeds[sheet.slot]}
          career={careers[playerAt(sheet.slot)!.id]}
          neighbours={(nbrs[sheet.slot] ?? []).map((n) => {
            const p = playerAt(n);
            return { slot: slotById(n), player: p, career: p ? careers[p.id] : undefined };
          })}
          locked={day.completed}
          onReplace={() => setSheet({ kind: "search", slot: sheet.slot })}
          onRemove={() => remove(sheet.slot)}
          onClose={() => setSheet(null)}
        />
      )}

      {puzzle && sheet?.kind === "result" && (
        <ResultSheet puzzle={puzzle} day={day} stats={date === today && today ? computeStats(today) : null} onClose={() => setSheet(null)} />
      )}
    </>
  );
}
