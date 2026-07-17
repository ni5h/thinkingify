import { PuzzleTier } from '../../../core/models/puzzle';

export interface TierConfig {
  tier: PuzzleTier;
  /** Expected time-to-answer at this tier, in ms. Must match the backend's
   * TIER_TARGET_TIME_MS for the same game — see api/app/services/puzzle_service.py. */
  targetTimeMs: number;
}

/**
 * Shared contract every game's generator/validator conforms to, so the Game
 * Shell and the rest of the puzzle infrastructure can work with any game
 * without knowing its internals.
 */
export interface PuzzleGame<TPuzzle, TAnswer> {
  gameId: string;
  tiers: TierConfig[];
  generate(tier: PuzzleTier): TPuzzle;
  validate(puzzle: TPuzzle, answer: TAnswer): boolean;
}
