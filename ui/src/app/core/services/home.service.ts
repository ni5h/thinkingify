import { Injectable, computed, inject } from '@angular/core';
import { BlogService } from './blog.service';
import { BrotherService } from './brother.service';
import { PuzzleProgressService } from './puzzle-progress.service';
import { ContentListItem } from '../models/content';
import { BrotherTierState } from '../models/brother';
import { GameStats } from '../models/puzzle';
import {
  KakoomaOperation,
  KAKOOMA_OPERATIONS,
  KAKOOMA_OPERATION_LABELS,
  KAKOOMA_OPERATION_DESCRIPTIONS,
  KAKOOMA_GAME_ID_PREFIX,
  isKakoomaGameId,
} from '../../features/sherlock/kakooma/kakooma.model';

export type ContinueRoom = 'rowling' | 'ramanujan' | 'sherlock';
export type StepState = 'done' | 'current' | 'upcoming';
export interface ContinueStep {
  state: StepState;
}

/**
 * The "Today's chapter" continue card on the home screen. Phase 0 feeds it from
 * the child's latest existing activity (a Rowling draft, the active Brothers
 * tier, or recent Kakooma practice). Phase 3 swaps the source to real concept
 * progress without changing this shape or the home UI.
 */
export interface ContinueCard {
  room: ContinueRoom;
  title: string;
  subtitle: string;
  steps: ContinueStep[];
  route: string[];
}

/** The "Crack it" card — one puzzle, for now the next Kakooma operation. */
export interface CrackItCard {
  operation: KakoomaOperation;
  label: string;
  prompt: string;
  route: string[];
}

const TRAIL_LENGTH = 5;

function trail(doneCount: number): ContinueStep[] {
  const done = Math.max(0, Math.min(doneCount, TRAIL_LENGTH));
  return Array.from({ length: TRAIL_LENGTH }, (_, i) => ({
    state: i < done ? 'done' : i === done ? 'current' : 'upcoming',
  }));
}

function operationOf(gameId: string): KakoomaOperation {
  return gameId.slice(KAKOOMA_GAME_ID_PREFIX.length) as KakoomaOperation;
}

/**
 * Pure selection so it's trivially testable: pick the most recent of a Rowling
 * draft or Kakooma practice (both carry timestamps); fall back to the active
 * Brothers tier; finally a sensible starter. Never null — the home always has a
 * Continue button.
 */
export function selectContinue(
  posts: ContentListItem[],
  brotherState: BrotherTierState[],
  kakoomaStats: GameStats[],
): ContinueCard {
  const latestDraft = posts
    .filter((p) => p.status === 'draft' && p.style !== 'diary_entry')
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at))[0];

  const latestKakooma = kakoomaStats
    .filter((s) => isKakoomaGameId(s.game_id) && s.last_attempt_at)
    .sort((a, b) => (b.last_attempt_at ?? '').localeCompare(a.last_attempt_at ?? ''))[0];

  const draftTs = latestDraft?.updated_at ?? '';
  const kakoomaTs = latestKakooma?.last_attempt_at ?? '';

  if (latestDraft && draftTs >= kakoomaTs) {
    return {
      room: 'rowling',
      title: latestDraft.title?.trim() || 'Your writing',
      subtitle: 'Pick up where you left off',
      steps: trail(2),
      route: ['/rowling/write', latestDraft.id],
    };
  }

  if (latestKakooma) {
    const op = operationOf(latestKakooma.game_id);
    return {
      room: 'sherlock',
      title: `${KAKOOMA_OPERATION_LABELS[op]} puzzles`,
      subtitle: 'Keep spotting the hidden answers',
      steps: trail(2),
      route: ['/sherlock/kakooma', op],
    };
  }

  const activeTier = brotherState.find((t) => t.status === 'active');
  if (activeTier) {
    const mastered = brotherState.filter((t) => t.status === 'mastered').length;
    return {
      room: 'ramanujan',
      title: `Brothers — ${activeTier.name}`,
      subtitle: 'Warm up your mental maths',
      steps: trail(mastered),
      route: ['/ramanujan/brothers'],
    };
  }

  // Nothing started yet — a calm entry point.
  return {
    room: 'ramanujan',
    title: 'Mental maths warm-up',
    subtitle: 'A gentle place to start thinking',
    steps: trail(0),
    route: ['/ramanujan/brothers'],
  };
}

/**
 * Phase 3 source: the child's real concept progress. Picks the first available
 * concept that isn't solid yet (the next thing to learn), with the trail showing
 * how many concepts in the chapter are solid. Returns null when there's no live
 * chapter content, so the caller falls back to selectContinue.
 */
export function selectConceptContinue(
  chapterTitle: string,
  concepts: { id: string; title: string; order_index: number }[],
  progress: { concept_id: string; state: string; available: boolean }[],
): ContinueCard | null {
  if (concepts.length === 0) return null;
  const byId = new Map(progress.map((p) => [p.concept_id, p]));
  const solid = progress.filter((p) => p.state === 'solid').length;
  const ordered = [...concepts].sort((a, b) => a.order_index - b.order_index);
  const next =
    ordered.find((c) => (byId.get(c.id)?.available ?? true) && byId.get(c.id)?.state !== 'solid') ??
    ordered.find((c) => byId.get(c.id)?.available ?? true);
  if (!next) return null;
  return {
    room: 'ramanujan',
    title: next.title,
    subtitle: chapterTitle,
    steps: trail(solid),
    route: ['/ramanujan/learn', next.id],
  };
}

/** The next Kakooma operation to try: least-recently practiced (unattempted first). */
export function selectCrackIt(kakoomaStats: GameStats[]): CrackItCard {
  const byId = new Map(kakoomaStats.map((s) => [s.game_id, s.last_attempt_at ?? '']));
  const op = [...KAKOOMA_OPERATIONS].sort(
    (a, b) =>
      (byId.get(`${KAKOOMA_GAME_ID_PREFIX}${a}`) ?? '').localeCompare(
        byId.get(`${KAKOOMA_GAME_ID_PREFIX}${b}`) ?? '',
      ),
  )[0];
  return {
    operation: op,
    label: KAKOOMA_OPERATION_LABELS[op],
    prompt: KAKOOMA_OPERATION_DESCRIPTIONS[op],
    route: ['/sherlock/kakooma', op],
  };
}

@Injectable({ providedIn: 'root' })
export class HomeService {
  private readonly blog = inject(BlogService);
  private readonly brothers = inject(BrotherService);
  private readonly puzzle = inject(PuzzleProgressService);

  readonly continueCard = computed<ContinueCard>(() =>
    selectContinue(this.blog.all() ?? [], this.brothers.state() ?? [], this.puzzle.stats() ?? []),
  );

  readonly crackIt = computed<CrackItCard>(() => selectCrackIt(this.puzzle.stats() ?? []));

  getContinue(): ContinueCard {
    return this.continueCard();
  }
}
