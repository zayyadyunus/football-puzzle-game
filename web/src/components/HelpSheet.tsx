"use client";

import Sheet from "./Sheet";

function Line({ color, dashed }: { color: string; dashed?: boolean }) {
  return (
    <svg width="34" height="10" aria-hidden className="shrink-0 rounded bg-[var(--pitch)]">
      <line x1="4" y1="5" x2="30" y2="5" stroke={color} strokeWidth={dashed ? 2 : 3} strokeDasharray={dashed ? "4 3" : undefined} strokeLinecap="round" />
    </svg>
  );
}

export default function HelpSheet({ onClose }: { onClose: () => void }) {
  return (
    <Sheet title="How to play" onClose={onClose}>
      <div className="space-y-4 px-5 py-4 text-[15px] leading-relaxed">
        <p>
          Complete the starting eleven. Every line on the pitch joins two players who must have been{" "}
          <strong>teammates</strong>: at the same club at the same time, or in the same senior national team.
        </p>
        <ul className="space-y-2">
          <li className="flex items-center gap-3">
            <Line color="var(--link-valid)" /> They played together
          </li>
          <li className="flex items-center gap-3">
            <Line color="var(--link-invalid)" /> Never teammates: try someone else
          </li>
          <li className="flex items-center gap-3">
            <Line color="rgb(255 255 255 / 0.7)" dashed /> Still waiting for a player
          </li>
        </ul>
        <ul className="list-disc space-y-1.5 pl-5 text-muted">
          <li>Dark shirts are pre-placed and can&apos;t be moved.</li>
          <li>Players must suit the position: goalkeepers in goal, defenders at the back, and so on. Wide roles accept midfielders or forwards.</li>
          <li>Any valid XI counts. There&apos;s no single right answer.</li>
          <li>There&apos;s no mistake limit, but wrong links are counted in your result.</li>
          <li>A new puzzle every day at midnight UK time. Easy on Monday, hardest at the weekend.</li>
        </ul>
        <button onClick={onClose} className="w-full rounded-full bg-accent py-3 font-semibold text-accent-ink">
          Let&apos;s play
        </button>
      </div>
    </Sheet>
  );
}
