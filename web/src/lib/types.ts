export type PosGroup = "GK" | "DEF" | "MID" | "FWD";

export interface Slot {
  id: string;
  label: string;
  x: number; // 0 left → 100 right
  y: number; // 0 own goal → 100 opponent's goal
  accepts: PosGroup[];
}

export interface Formation {
  name: string;
  slots: Slot[];
  links: [string, string][];
}

export interface PlayerCard {
  id: string;
  name: string;
  nat: string | null;
  pos: PosGroup[];
  born: number | null;
  career: [number, number] | null;
}

export interface Puzzle {
  date: string;
  difficulty: { label: string; knowledge: number; solutions: Record<string, number> };
  formation: Formation;
  seeds: Record<string, PlayerCard>;
  solution: Record<string, PlayerCard>;
  solution_links: { a: string; b: string; via: { team: string; kind: string; from: number; to: number }[] }[];
}

/** [teamId, teamName, isNationalTeam, start, end] — start/end are fractional years */
export type Spell = [string, string, boolean, number, number];

export interface LinkVia {
  team: string;
  national: boolean;
  from: number;
  to: number;
}

export type LinkState = "pending" | "valid" | "invalid";
