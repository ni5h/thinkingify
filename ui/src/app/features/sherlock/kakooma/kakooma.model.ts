export type KakoomaOperation = 'add' | 'subtract' | 'multiply' | 'divide';

export interface KakoomaPuzzle {
  numbers: number[];
  // Subtract/divide are non-commutative, and for any valid triple
  // (a, b, target) where target = a - b, it's a mathematical identity that
  // a - target = b too (same for division: a/target = b) — so those two
  // operations always have exactly 2 legitimately-correct tap positions,
  // not 1. Add/multiply have no such identity, so this array always has
  // exactly 1 entry for them. See kakooma.engine.ts's countValidPairs.
  answerIndices: number[];
  operation: KakoomaOperation;
}

export const KAKOOMA_OPERATIONS: KakoomaOperation[] = ['add', 'subtract', 'multiply', 'divide'];

export const KAKOOMA_GAME_ID_PREFIX = 'kakooma-';

export function isKakoomaGameId(gameId: string): boolean {
  return gameId.startsWith(KAKOOMA_GAME_ID_PREFIX);
}

export const KAKOOMA_OPERATION_LABELS: Record<KakoomaOperation, string> = {
  add: 'Addition',
  subtract: 'Subtraction',
  multiply: 'Multiplication',
  divide: 'Division',
};

export const KAKOOMA_OPERATION_VERBS: Record<KakoomaOperation, string> = {
  add: 'sum',
  subtract: 'difference',
  multiply: 'product',
  divide: 'quotient',
};

export const KAKOOMA_OPERATION_DESCRIPTIONS: Record<KakoomaOperation, string> = {
  add: 'Spot the sum hiding in a group of numbers.',
  subtract: 'Spot the difference hiding in a group of numbers.',
  multiply: 'Spot the product hiding in a group of numbers.',
  divide: 'Spot the quotient hiding in a group of numbers.',
};
