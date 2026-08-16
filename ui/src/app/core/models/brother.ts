export type BrotherTierStatus = 'locked' | 'active' | 'mastered';

export interface BrotherTierState {
  tier_id: string;
  name: string;
  status: BrotherTierStatus;
  baseline_ms: number | null;
  median_ms: number | null;
  accuracy: number | null;
  attempts_count: number;
}

export interface BrotherQuestion {
  index: number;
  tier_id: string;
  number: number;
  active_digits: number;
}

export interface BrotherSession {
  id: string;
  questions: BrotherQuestion[];
}

export interface BrotherAnswerResult {
  correct: boolean;
  correct_answer: number;
  mastered_tier_id: string | null;
  unlocked_tier_id: string | null;
}
