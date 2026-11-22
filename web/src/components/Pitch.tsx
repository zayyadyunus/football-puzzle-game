"use client";

import type { Formation, LinkState, PlayerCard, Slot } from "@/lib/types";
import { shortName } from "@/lib/links";

export interface SlotView {
  slot: Slot;
  player: PlayerCard | null;
  seed: boolean;
  hasInvalid: boolean;
  fresh: boolean; // just placed: play the pop animation
}

interface Props {
  formation: Formation;
  slots: SlotView[];
  links: { a: string; b: string; state: LinkState }[];
  onSlot: (slotId: string) => void;
}

/** Formation y (0 own goal → 100 attack) to % from the top of the pitch box. */
const top = (y: number) => 7 + (92 - y) * 0.92;

const SHIRT =
  "M16 6 L9 8.5 L2.5 15.5 L8 21.5 L12 18.5 L12 42 L36 42 L36 18.5 L40 21.5 L45.5 15.5 L39 8.5 L32 6 C31 9.2 28 11.2 24 11.2 C20 11.2 17 9.2 16 6 Z";

function Shirt({ kind }: { kind: "seed" | "user" | "empty" }) {
  return (
    <svg viewBox="0 0 48 48" className="h-11 w-11 drop-shadow-[0_2px_2px_rgba(0,0,0,0.25)]" aria-hidden>
      {kind === "empty" ? (
        <>
          <path d={SHIRT} fill="rgb(255 255 255 / 0.12)" stroke="rgb(255 255 255 / 0.85)" strokeWidth="1.6" strokeDasharray="3 2.4" />
          <path d="M24 21v12M18 27h12" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
        </>
      ) : (
        <path
          d={SHIRT}
          fill={kind === "seed" ? "var(--seed-shirt)" : "var(--user-shirt)"}
          stroke={kind === "seed" ? "rgb(255 255 255 / 0.25)" : "rgb(0 0 0 / 0.12)"}
          strokeWidth="1"
        />
      )}
    </svg>
  );
}

function Markings() {
  return (
    <svg viewBox="0 0 80 100" className="pointer-events-none absolute inset-0 h-full w-full" aria-hidden>
      <g fill="none" stroke="var(--pitch-line)" strokeWidth="0.5">
        <rect x="2" y="2" width="76" height="96" />
        <line x1="2" y1="50" x2="78" y2="50" />
        <circle cx="40" cy="50" r="8.5" />
        <rect x="18" y="83" width="44" height="15" />
        <rect x="30" y="93" width="20" height="5" />
        <path d="M33.13 83 A8.5 8.5 0 0 1 46.87 83" />
        <rect x="18" y="2" width="44" height="15" />
        <rect x="30" y="2" width="20" height="5" />
        <path d="M33.13 17 A8.5 8.5 0 0 0 46.87 17" />
      </g>
      <g fill="var(--pitch-line)">
        <circle cx="40" cy="50" r="0.6" />
        <circle cx="40" cy="88" r="0.5" />
        <circle cx="40" cy="12" r="0.5" />
      </g>
    </svg>
  );
}

export default function Pitch({ formation, slots, links, onSlot }: Props) {
  const pos = Object.fromEntries(formation.slots.map((s) => [s.id, s]));
  return (
    <div className="pitch relative aspect-[4/5] w-full select-none overflow-hidden rounded-2xl">
      <Markings />

      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="pointer-events-none absolute inset-0 h-full w-full" aria-hidden>
        {links.map(({ a, b, state }) => (
          <line
            key={`${a}-${b}`}
            x1={pos[a].x}
            y1={top(pos[a].y)}
            x2={pos[b].x}
            y2={top(pos[b].y)}
            vectorEffect="non-scaling-stroke"
            strokeLinecap="round"
            stroke={state === "valid" ? "var(--link-valid)" : state === "invalid" ? "var(--link-invalid)" : "var(--link-pending)"}
            strokeWidth={state === "pending" ? 2 : 3.5}
            strokeDasharray={state === "pending" ? "5 5" : undefined}
            style={{ transition: "stroke 200ms" }}
          />
        ))}
      </svg>

      {slots.map(({ slot, player, seed, hasInvalid, fresh }) => {
        const label = player ? shortName(player.name) : slot.label;
        const aria = player
          ? `${slot.label}: ${player.name}${seed ? " (pre-placed)" : ""}${hasInvalid ? ", has a broken link" : ""}`
          : `Empty ${slot.label} slot — pick a player`;
        return (
          <button
            key={slot.id}
            onClick={() => onSlot(slot.id)}
            aria-label={aria}
            className="group absolute flex w-[84px] -translate-x-1/2 -translate-y-[22px] flex-col items-center gap-0.5 rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-white"
            style={{ left: `${slot.x}%`, top: `${top(slot.y)}%` }}
          >
            <span className={`${fresh ? "anim-pop" : ""} transition-transform group-active:scale-95`}>
              <Shirt kind={player ? (seed ? "seed" : "user") : "empty"} />
            </span>
            <span
              className={`max-w-full truncate rounded-[5px] px-1.5 py-[2px] text-[11px] font-semibold leading-tight shadow-sm ${
                !player
                  ? "bg-black/30 text-white"
                  : hasInvalid
                    ? "bg-[var(--link-invalid)] text-white"
                    : seed
                      ? "bg-[#121212] text-white"
                      : "bg-white text-[#121212]"
              }`}
            >
              {label}
            </span>
          </button>
        );
      })}
    </div>
  );
}
