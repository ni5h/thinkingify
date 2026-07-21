export const PUZZLE_TIERS = ['trial', 'beginner', 'intermediate', 'advanced', 'pro'] as const;
export type PuzzleTier = (typeof PUZZLE_TIERS)[number];

const TIER_LABELS: Record<PuzzleTier, string> = {
  trial: 'Trial',
  beginner: 'Beginner',
  intermediate: 'Intermediate',
  advanced: 'Advanced',
  pro: 'Pro',
};

export function tierLabel(tier: PuzzleTier): string {
  return TIER_LABELS[tier];
}

export interface GameProgress {
  game_id: string;
  current_tier: PuzzleTier;
  variations_completed: number;
  variations_per_tier: number;
  highest_tier_unlocked: PuzzleTier;
  updated_at: string;
}

export interface AttemptCreate {
  started_at: string;
  completed_at: string;
  time_taken_ms: number;
  correct: boolean;
  // Set to practice an already-passed tier without touching real
  // progression — must be strictly earlier than the current tier,
  // enforced server-side. See api/app/services/puzzle_service.py.
  practice_tier?: PuzzleTier;
}

export interface AttemptOut {
  id: string;
  game_id: string;
  tier: PuzzleTier;
  variation_index: number;
  started_at: string;
  completed_at: string;
  time_taken_ms: number;
  correct: boolean;
  beat_time_limit: boolean;
  created_at: string;
}

export interface AttemptResult {
  attempt: AttemptOut;
  progress: GameProgress;
  tier_advanced: boolean;
}

// Effort-focused stats — counts and time invested, never an accuracy
// percentage or "best time". See api/app/schemas/puzzle.py's GameStatsOut.
export interface GameStats {
  game_id: string;
  current_tier: PuzzleTier;
  total_attempts: number;
  attempts_today: number;
  attempts_this_week: number;
  total_time_ms: number;
  last_attempt_at: string | null;
}

// Per-tier breakdown for one game — the one deliberate exception to "no
// best time anywhere": fastest_time_ms is strictly self-referential (never
// compared to anyone else). See api/app/schemas/puzzle.py's TierStatsOut.
export interface TierStats {
  tier: PuzzleTier;
  attempts: number;
  fastest_time_ms: number | null;
}
