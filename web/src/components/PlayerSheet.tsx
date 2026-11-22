"use client";

import Sheet from "./Sheet";
import { formatVia, sharedTeams, teamLabel, yearSpan } from "@/lib/links";
import type { PlayerCard, Slot, Spell } from "@/lib/types";

interface Props {
  slot: Slot;
  player: PlayerCard;
  seed: boolean;
  career: Spell[] | undefined;
  neighbours: { slot: Slot; player: PlayerCard | null; career: Spell[] | undefined }[];
  locked: boolean; // puzzle finished
  onReplace: () => void;
  onRemove: () => void;
  onClose: () => void;
}

export default function PlayerSheet({ slot, player, seed, career, neighbours, locked, onReplace, onRemove, onClose }: Props) {
  const clubs = (career ?? []).filter((s) => !s[2]);
  const nats = (career ?? []).filter((s) => s[2]);
  return (
    <Sheet
      onClose={onClose}
      title={player.name}
      subtitle={
        <>
          {[slot.label, player.nat, player.career && `${player.career[0]}–${player.career[1]}`].filter(Boolean).join(" · ")}
          {seed && <span className="ml-2 rounded-full bg-ink px-2 py-0.5 text-xs font-semibold text-bg">Pre-placed</span>}
        </>
      }
    >
      <div className="space-y-5 px-5 py-4">
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted">Links</h3>
          <ul className="space-y-1.5">
            {neighbours.map(({ slot: ns, player: np, career: nc }) => {
              const via = np && career && nc ? sharedTeams(career, nc) : null;
              const state = !np ? "empty" : !via ? "loading" : via.length ? "valid" : "invalid";
              return (
                <li key={ns.id} className="flex items-start gap-2.5 text-sm">
                  <span
                    className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-bold ${
                      state === "valid" ? "bg-good text-white" : state === "invalid" ? "bg-bad text-white" : "border border-dashed border-muted text-muted"
                    }`}
                    aria-hidden
                  >
                    {state === "valid" ? "✓" : state === "invalid" ? "✕" : ""}
                  </span>
                  <span className="min-w-0">
                    <span className="font-semibold">{np ? np.name : `Empty ${ns.label}`}</span>
                    <span className="block text-muted">
                      {state === "empty" && "Not picked yet"}
                      {state === "loading" && "Checking…"}
                      {state === "invalid" && "Never teammates"}
                      {state === "valid" && via!.map(formatVia).join("; ")}
                    </span>
                  </span>
                </li>
              );
            })}
          </ul>
        </section>

        {career && (
          <section>
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted">Career</h3>
            <ul className="divide-y divide-line rounded-xl border border-line text-sm">
              {[...clubs, ...nats].map(([id, name, nat, a, b], i) => (
                <li key={`${id}-${i}`} className="flex justify-between gap-3 px-3 py-2">
                  <span className="truncate">
                    {teamLabel(name, nat)}
                    {nat && <span className="text-muted"> · national team</span>}
                  </span>
                  <span className="shrink-0 tabular-nums text-muted">
                    {yearSpan(a, b, b >= new Date().getFullYear() + 0.5)}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {!seed && !locked && (
          <div className="flex gap-2 pt-1">
            <button onClick={onReplace} className="flex-1 rounded-full bg-accent py-3 font-semibold text-accent-ink">
              Replace
            </button>
            <button onClick={onRemove} className="flex-1 rounded-full border border-ink py-3 font-semibold">
              Remove
            </button>
          </div>
        )}
      </div>
    </Sheet>
  );
}
