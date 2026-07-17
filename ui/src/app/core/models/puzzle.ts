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
