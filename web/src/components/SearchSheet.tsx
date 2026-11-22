"use client";

import { useEffect, useRef, useState } from "react";
import Sheet from "./Sheet";
import { searchPlayers, type SearchResult } from "@/lib/data";
import { fitsSlot } from "@/lib/links";
import type { PlayerCard, Slot } from "@/lib/types";

interface Props {
  slot: Slot;
  neighbours: PlayerCard[];
  usedIds: Set<string>;
  onPick: (p: PlayerCard) => void;
  onClose: () => void;
}

const GROUP_NAME: Record<string, string> = { GK: "goalkeeper", DEF: "defender", MID: "midfielder", FWD: "forward" };

export function playerMeta(p: PlayerCard) {
  const bits = [p.nat, p.pos.join("/") || null, p.career ? `${p.career[0]}–${p.career[1]}` : null];
  return bits.filter(Boolean).join(" · ");
}

export default function SearchSheet({ slot, neighbours, usedIds, onPick, onClose }: Props) {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const reqId = useRef(0);

  useEffect(() => {
    const query = q.trim();
    const id = ++reqId.current;
    if (query.length < 3) {
      // 2-letter names (e.g. "Zé") are only found once the query has another word or 3+ letters.
      const t = setTimeout(() => id === reqId.current && setResults(null), 0);
      return () => clearTimeout(t);
    }
    const t = setTimeout(async () => {
      setLoading(true);
      const r = await searchPlayers(query);
      if (id === reqId.current) {
        setResults(r);
        setLoading(false);
      }
    }, 120);
    return () => clearTimeout(t);
  }, [q]);

  const accepts = slot.accepts.map((g) => GROUP_NAME[g]).join(" or ");

  return (
    <Sheet
      tall
      onClose={onClose}
      title={`Pick a ${slot.label}`}
      subtitle={
        neighbours.length ? (
          <>
            Must have played with{" "}
            {neighbours.map((n, i) => (
              <span key={n.id}>
                <span className="font-semibold text-ink">{n.name}</span>
                {i < neighbours.length - 2 ? ", " : i === neighbours.length - 2 ? " and " : ""}
              </span>
            ))}
          </>
        ) : (
          <>Any {accepts}. Its neighbours are still empty.</>
        )
      }
    >
      <div className="sticky top-0 z-10 bg-surface px-5 pb-2 pt-3">
        <label className="relative block">
          <span className="sr-only">Search players</span>
          <svg className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" width="18" height="18" viewBox="0 0 20 20" aria-hidden>
            <circle cx="9" cy="9" r="6" fill="none" stroke="currentColor" strokeWidth="1.8" />
            <path d="M13.5 13.5L17 17" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          </svg>
          <input
            autoFocus
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search any player…"
            autoComplete="off"
            autoCorrect="off"
            spellCheck={false}
            enterKeyHint="search"
            className="w-full rounded-xl border border-line bg-bg py-3 pl-10 pr-3 text-base outline-none placeholder:text-muted focus:border-ink"
          />
        </label>
        <p className="mt-2 text-xs text-muted">
          {accepts[0].toUpperCase() + accepts.slice(1)}s only. There&apos;s no penalty for a wrong link: you&apos;ll see it go red.
        </p>
      </div>

      <ul className="px-2 pb-4" aria-live="polite">
        {results === null && !loading && (
          <li className="px-3 py-8 text-center text-sm text-muted">Type at least 3 letters of a name.</li>
        )}
        {results?.length === 0 && !loading && (
          <li className="px-3 py-8 text-center text-sm text-muted">No players found for “{q.trim()}”.</li>
        )}
        {results?.map((p) => {
          const used = usedIds.has(p.id);
          const fits = fitsSlot(p, slot);
          const disabled = used || !fits;
          return (
            <li key={p.id}>
              <button
                disabled={disabled}
                onClick={() => onPick(p)}
                className="flex w-full items-center justify-between gap-3 rounded-xl px-3 py-2.5 text-left hover:bg-bg disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:bg-transparent"
              >
                <span className="min-w-0">
                  <span className="block truncate font-semibold">{p.name}</span>
                  <span className="block truncate text-sm text-muted">{playerMeta(p)}</span>
                </span>
                {disabled && (
                  <span className="shrink-0 rounded-full border border-line px-2 py-0.5 text-xs text-muted">
                    {used ? "In your XI" : `Not a ${slot.accepts.map((g) => GROUP_NAME[g]).join("/")}`}
                  </span>
                )}
              </button>
            </li>
          );
        })}
      </ul>
    </Sheet>
  );
}
