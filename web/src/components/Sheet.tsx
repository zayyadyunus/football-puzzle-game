"use client";

import { useEffect, useId, useRef } from "react";

interface Props {
  title: string;
  subtitle?: React.ReactNode;
  onClose: () => void;
  children: React.ReactNode;
  /** Fill most of the viewport height (e.g. search results) */
  tall?: boolean;
}

/** Bottom sheet on phones, centred dialog on wider screens. Escape / backdrop closes. */
export default function Sheet({ title, subtitle, onClose, children, tall }: Props) {
  const titleId = useId();
  const panel = useRef<HTMLDivElement>(null);
  // Keep the latest onClose without re-running the mount effect (which manages focus + scroll lock).
  const close = useRef(onClose);
  useEffect(() => {
    close.current = onClose;
  });

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && close.current();
    window.addEventListener("keydown", onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const prevFocus = document.activeElement as HTMLElement | null;
    if (!panel.current?.contains(document.activeElement)) panel.current?.focus();
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
      prevFocus?.focus?.();
    };
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center" role="presentation">
      <div className="anim-fade absolute inset-0 bg-black/45" onClick={onClose} aria-hidden />
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className={`anim-sheet relative flex w-full max-w-[480px] flex-col rounded-t-2xl bg-surface text-ink shadow-2xl outline-none sm:rounded-2xl ${
          tall ? "h-[85dvh] sm:h-[640px]" : "max-h-[85dvh]"
        }`}
      >
        <div className="flex items-start justify-between gap-3 border-b border-line px-5 pb-3 pt-4">
          <div className="min-w-0">
            <h2 id={titleId} className="font-serif text-xl font-semibold leading-tight">
              {title}
            </h2>
            {subtitle && <div className="mt-1 text-sm text-muted">{subtitle}</div>}
          </div>
          <button
            onClick={onClose}
            className="-mr-2 -mt-1 rounded-full p-2 text-muted hover:bg-line/60 hover:text-ink"
            aria-label="Close"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden>
              <path d="M5 5l10 10M15 5L5 15" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
      </div>
    </div>
  );
}
