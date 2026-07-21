import { PUZZLE_TIERS, PuzzleTier } from '../../../core/models/puzzle';
import { PuzzleGame, TierConfig } from '../models/puzzle-game.model';
import { KakoomaOperation, KakoomaPuzzle } from './kakooma.model';

// Per-operation difficulty curves. multiply/divide use a visibly smaller
// operand range than add/subtract since products/quotients grow much
// faster — divide's range is the divisor/quotient range, not the dividend,
// mirroring how multiply's range is the two factors, not the product.
// Explicitly tunable later once there's real play data, same caveat the
// original single-Kakooma tuning carried.
interface TierShape {
  groupSize: number;
  operandRange: [number, number];
}

const TIER_SHAPES: Record<KakoomaOperation, Record<PuzzleTier, TierShape>> = {
  add: {
    trial: { groupSize: 4, operandRange: [1, 9] },
    beginner: { groupSize: 4, operandRange: [1, 9] },
    intermediate: { groupSize: 5, operandRange: [10, 99] },
    advanced: { groupSize: 6, operandRange: [10, 99] },
    pro: { groupSize: 6, operandRange: [10, 99] },
  },
  subtract: {
    trial: { groupSize: 4, operandRange: [1, 9] },
    beginner: { groupSize: 4, operandRange: [1, 9] },
    intermediate: { groupSize: 5, operandRange: [10, 99] },
    advanced: { groupSize: 6, operandRange: [10, 99] },
    pro: { groupSize: 6, operandRange: [10, 99] },
  },
  multiply: {
    trial: { groupSize: 4, operandRange: [1, 5] },
    beginner: { groupSize: 4, operandRange: [1, 9] },
    intermediate: { groupSize: 5, operandRange: [2, 9] },
    advanced: { groupSize: 6, operandRange: [2, 12] },
    pro: { groupSize: 6, operandRange: [2, 12] },
  },
  divide: {
    trial: { groupSize: 4, operandRange: [1, 5] },
    beginner: { groupSize: 4, operandRange: [1, 9] },
    intermediate: { groupSize: 5, operandRange: [2, 9] },
    advanced: { groupSize: 6, operandRange: [2, 12] },
    pro: { groupSize: 6, operandRange: [2, 12] },
  },
};

// Must stay in sync with the backend's TIER_TARGET_TIME_MS
// (api/app/services/puzzle_service.py) — see that file's comment for why
// this duplication exists.
const TIER_TARGET_TIME_MS: Record<KakoomaOperation, Record<PuzzleTier, number>> = {
  add: { trial: 20_000, beginner: 12_000, intermediate: 15_000, advanced: 25_000, pro: 15_000 },
  subtract: { trial: 20_000, beginner: 12_000, intermediate: 15_000, advanced: 25_000, pro: 15_000 },
  multiply: { trial: 20_000, beginner: 12_000, intermediate: 18_000, advanced: 28_000, pro: 18_000 },
  divide: { trial: 20_000, beginner: 12_000, intermediate: 18_000, advanced: 28_000, pro: 18_000 },
};

interface GeneratedTriple {
  a: number;
  b: number;
  target: number;
}

interface OperationDef {
  commutative: boolean;
  // How many valid pairs a freshly-generated (a,b,target) triple produces
  // BEFORE any distractors are added. 1 for add/multiply. For subtract and
  // divide this is unavoidably 2 — it's a mathematical identity that
  // target = a - b implies a - target = b (same for division), so both b
  // and target are always legitimately "the result of combining two
  // others." The generator accepts exactly this many, and rejects if a
  // distractor coincidentally creates any more.
  expectedValidPairs: number;
  /** Produce a valid (a, b, target = a <op> b) triple from the given
   * operand range, or null if this attempt should be retried. */
  generateTriple(min: number, max: number): GeneratedTriple | null;
  /** Test whether x <op> y is a valid combination, used for the
   * ambiguity check against arbitrary group members. Null = invalid
   * (e.g. non-integer division). */
  apply(x: number, y: number): number | null;
}

const OPERATIONS: Record<KakoomaOperation, OperationDef> = {
  add: {
    commutative: true,
    expectedValidPairs: 1,
    generateTriple: (min, max) => {
      const a = randomInt(min, max);
      const b = randomInt(min, max);
      return { a, b, target: a + b };
    },
    apply: (x, y) => x + y,
  },
  subtract: {
    commutative: false,
    expectedValidPairs: 2,
    generateTriple: (min, max) => {
      let a = randomInt(min, max);
      let b = randomInt(min, max);
      if (a === b) return null; // difference would be 0 — not a valid group number
      if (a < b) [a, b] = [b, a];
      const target = a - b;
      // target === b (a is exactly double b) means two DIFFERENT tiles
      // would show the identical number — numbers.indexOf can't tell them
      // apart, silently losing one of the two valid answer positions.
      // Simplest fix: don't generate this case, same as the a===b guard.
      if (target === b) return null;
      return { a, b, target };
    },
    apply: (x, y) => x - y,
  },
  multiply: {
    commutative: true,
    expectedValidPairs: 1,
    generateTriple: (min, max) => {
      const a = randomInt(min, max);
      const b = randomInt(min, max);
      return { a, b, target: a * b };
    },
    apply: (x, y) => x * y,
  },
  divide: {
    commutative: false,
    expectedValidPairs: 2,
    generateTriple: (min, max) => {
      const divisor = randomInt(min, max);
      const quotient = randomInt(min, max);
      if (divisor === 1 || quotient === 1) return null; // trivial ("divide by 1") — retry
      if (divisor === quotient) return null; // same numeric-identity issue as subtract, see there
      return { a: divisor * quotient, b: divisor, target: quotient };
    },
    apply: (x, y) => (y !== 0 && x % y === 0 ? x / y : null),
  },
};

const MAX_GENERATION_ATTEMPTS = 50;

export class KakoomaEngine implements PuzzleGame<KakoomaPuzzle, number> {
  readonly gameId: string;
  readonly tiers: TierConfig[];
  private readonly op: OperationDef;

  constructor(readonly operation: KakoomaOperation) {
    this.gameId = `kakooma-${operation}`;
    this.op = OPERATIONS[operation];
    this.tiers = PUZZLE_TIERS.map((tier) => ({ tier, targetTimeMs: TIER_TARGET_TIME_MS[operation][tier] }));
  }

  generate(tier: PuzzleTier): KakoomaPuzzle {
    const shape = TIER_SHAPES[this.operation][tier] ?? TIER_SHAPES[this.operation]['trial'];

    for (let attempt = 0; attempt < MAX_GENERATION_ATTEMPTS; attempt++) {
      const puzzle = this.tryGenerate(shape);
      if (puzzle) return puzzle;
    }
    throw new Error(`Failed to generate a valid Kakooma (${this.operation}) puzzle after max attempts`);
  }

  validate(puzzle: KakoomaPuzzle, answer: number): boolean {
    return puzzle.answerIndices.includes(answer);
  }

  private tryGenerate(shape: TierShape): KakoomaPuzzle | null {
    const [min, max] = shape.operandRange;
    const triple = this.op.generateTriple(min, max);
    if (!triple) return null;
    const { a, b, target } = triple;

    // Distractors must straddle target, not just cap out at it — target
    // (the sum/product) is mathematically almost always the largest of the
    // three numbers for add/multiply, so sampling only up to target left
    // "tap the biggest number" working as a reliable shortcut. Widening the
    // range symmetrically around target gives distractors a real chance of
    // landing above it too.
    const spread = Math.max(max - min, 1);
    const distractorMin = Math.max(1, target - spread);
    const distractorMax = target + spread;
    const used = new Set([a, b, target]);
    const distractors: number[] = [];

    while (distractors.length < shape.groupSize - 3) {
      const candidate = randomInt(distractorMin, distractorMax);
      if (used.has(candidate)) continue;
      used.add(candidate);
      distractors.push(candidate);
    }

    const numbers = shuffle([a, b, target, ...distractors]);

    // Reject groups where a distractor coincidentally forms an extra valid
    // relationship beyond the operation's unavoidable minimum (1 for
    // add/multiply, 2 for subtract/divide — see expectedValidPairs).
    if (countValidPairs(numbers, this.op) !== this.op.expectedValidPairs) return null;

    const answerIndices =
      this.op.expectedValidPairs === 1
        ? [numbers.indexOf(target)]
        : [numbers.indexOf(target), numbers.indexOf(b)];

    return { numbers, answerIndices, operation: this.operation };
  }
}

function countValidPairs(numbers: number[], op: OperationDef): number {
  let count = 0;
  for (let i = 0; i < numbers.length; i++) {
    for (let j = i + 1; j < numbers.length; j++) {
      // Non-commutative operations (subtract/divide) must be checked in
      // both directions per unordered pair — numbers[i] - numbers[j] and
      // numbers[j] - numbers[i] are different candidate answers.
      const candidates = op.commutative
        ? [op.apply(numbers[i], numbers[j])]
        : [op.apply(numbers[i], numbers[j]), op.apply(numbers[j], numbers[i])];

      for (const combined of candidates) {
        if (combined === null) continue;
        if (numbers.some((n, k) => k !== i && k !== j && n === combined)) count++;
      }
    }
  }
  return count;
}

function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function shuffle<T>(items: T[]): T[] {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = randomInt(0, i);
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}
