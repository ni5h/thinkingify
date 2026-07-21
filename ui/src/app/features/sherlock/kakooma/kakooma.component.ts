import { Component, computed, effect, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { PuzzleProgressService } from '../../../core/services/puzzle-progress.service';
import { PUZZLE_TIERS, PuzzleTier, tierLabel } from '../../../core/models/puzzle';
import { StorageService } from '../../../core/services/storage.service';
import { FeedbackState } from '../shared/feedback-toast.component';
import { GameShellComponent } from '../shared/game-shell.component';
import { formatTimePracticed } from '../shared/puzzle-format.util';
import { KakoomaEngine } from './kakooma.engine';
import {
  KAKOOMA_OPERATIONS,
  KAKOOMA_OPERATION_LABELS,
  KAKOOMA_OPERATION_VERBS,
  KakoomaOperation,
  KakoomaPuzzle,
} from './kakooma.model';

const FEEDBACK_DELAY_MS = 1200;

function isKakoomaOperation(value: string | null): value is KakoomaOperation {
  return !!value && (KAKOOMA_OPERATIONS as string[]).includes(value);
}

function formatFastest(ms: number | null): string {
  return ms === null ? '—' : `${(ms / 1000).toFixed(1)}s`;
}

interface TierRow {
  tier: PuzzleTier;
  label: string;
  attempts: number;
  fastestLabel: string;
}

@Component({
  selector: 'app-kakooma',
  standalone: true,
  imports: [RouterLink, GameShellComponent],
  template: `
    <a routerLink="/sherlock" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
      &larr; Back to puzzles
    </a>

    @if (myStats(); as s) {
      <p class="text-center text-xs text-muted font-mono mt-4">
        {{ s.attempts_today }} today &middot; {{ s.total_attempts }} all-time &middot; {{ timePracticed() }} practiced
      </p>
    }

    <div class="mt-6">
      @if (puzzle(); as p) {
        <app-game-shell
          [gameTitle]="gameTitle()"
          [tierLabel]="tierLabelText()"
          [variationsCompleted]="variationsCompleted()"
          [variationsPerTier]="10"
          [progressOverride]="practiceProgressText()"
          [streak]="streak()"
          [running]="isAnswering()"
          [feedback]="feedback()"
          [awaitingStart]="awaitingStart()"
          (start)="confirmStart()"
        >
          <p class="text-center text-muted mb-6">
            Tap the number that's the {{ verb() }} of two others.
          </p>
          <div class="grid grid-cols-2 gap-4">
            @for (n of p.numbers; track $index) {
              <button
                type="button"
                class="font-mono text-2xl font-bold py-6 rounded-xl bg-cloud/60 hover:bg-cloud active:scale-95 transition disabled:opacity-50"
                [disabled]="!isAnswering()"
                (click)="select($index)"
              >
                {{ n }}
              </button>
            }
          </div>
        </app-game-shell>

        @if (tierAdvancedMessage()) {
          <p class="text-center text-moss-dark font-medium mt-4">{{ tierAdvancedMessage() }}</p>
        }
        @if (fasterMessage()) {
          <p class="text-center text-moss-dark font-medium mt-4">{{ fasterMessage() }}</p>
        }
      }

      @if (practiceTier()) {
        <div class="text-center mt-4">
          <button
            type="button"
            class="rounded-xl border border-cloud bg-paper px-5 py-2.5 text-sm font-medium text-ink hover:border-moss hover:bg-cloud/60 transition-colors"
            (click)="exitPractice()"
          >
            Back to {{ tierLabel(tier()) }}
          </button>
        </div>
      } @else if (tierRows().length && isAnswering()) {
        <div class="mt-6 rounded-2xl border border-cloud bg-white shadow-sm p-4 max-w-xl mx-auto">
          <p class="text-xs font-medium text-muted mb-3">Your times by tier</p>
          <ul class="space-y-2">
            @for (row of tierRows(); track row.tier) {
              <li class="flex items-center justify-between text-sm">
                <span class="text-ink">{{ row.label }}</span>
                <span class="font-mono text-muted">{{ row.fastestLabel }}</span>
                @if (row.tier !== tier()) {
                  <button
                    type="button"
                    class="rounded-lg px-2 py-1 text-xs font-medium text-moss hover:bg-moss/10 transition-colors"
                    (click)="enterPractice(row.tier)"
                  >
                    Practice
                  </button>
                }
              </li>
            }
          </ul>
        </div>
      }
    </div>
  `,
})
export default class KakoomaComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly puzzleProgress = inject(PuzzleProgressService);
  private readonly storage = inject(StorageService);

  private readonly operation: KakoomaOperation;
  private readonly engine: KakoomaEngine;
  private readonly progress;
  private readonly tierStats;

  readonly gameTitle = computed(() => `Kakooma — ${KAKOOMA_OPERATION_LABELS[this.operation]}`);
  readonly verb = computed(() => KAKOOMA_OPERATION_VERBS[this.operation]);

  readonly myStats = computed(() =>
    (this.puzzleProgress.stats() ?? []).find((s) => s.game_id === this.engine.gameId)
  );
  readonly timePracticed = computed(() => formatTimePracticed(this.myStats()?.total_time_ms ?? 0));

  readonly tier = signal<PuzzleTier>('trial');
  readonly variationsCompleted = signal(0);

  // Practicing an earlier tier is a separate mode that never touches real
  // progression (tier/variationsCompleted above) — see kakooma_service's
  // record_attempt on the backend for the enforcement side of this.
  readonly practiceTier = signal<PuzzleTier | null>(null);
  readonly activeTier = computed(() => this.practiceTier() ?? this.tier());
  readonly tierLabelText = computed(() =>
    this.practiceTier() ? `Practicing: ${tierLabel(this.practiceTier()!)}` : tierLabel(this.tier())
  );

  // Session-local "how many times have I retried" counter — practice mode
  // never touches variationsCompleted, so this fills the gap that would
  // otherwise leave the header frozen at "0/10" the whole practice session.
  readonly practiceAttemptCount = signal(0);
  readonly practiceProgressText = computed(() =>
    this.practiceTier() ? `Attempt ${this.practiceAttemptCount()}` : null
  );

  readonly tierLabel = tierLabel;

  readonly tierRows = computed<TierRow[]>(() => {
    const statsByTier = new Map((this.tierStats.value() ?? []).map((s) => [s.tier, s]));
    const currentIndex = PUZZLE_TIERS.indexOf(this.tier());
    return PUZZLE_TIERS.filter((_, i) => i <= currentIndex).map((t) => {
      const stats = statsByTier.get(t);
      return {
        tier: t,
        label: tierLabel(t),
        attempts: stats?.attempts ?? 0,
        fastestLabel: formatFastest(stats?.fastest_time_ms ?? null),
      };
    });
  });

  readonly streak = signal(0);
  readonly feedback = signal<FeedbackState>(null);
  readonly puzzle = signal<KakoomaPuzzle | null>(null);
  readonly tierAdvancedMessage = signal<string | null>(null);
  readonly fasterMessage = signal<string | null>(null);

  // Every round waits for an explicit tap before the scoring clock starts —
  // fairer timing, since a learner shouldn't be penalized for not being
  // ready the instant a puzzle is generated.
  readonly awaitingStart = signal(true);
  readonly isAnswering = computed(() => this.feedback() === null && !this.awaitingStart());

  private startedAt = 0;
  private initialized = false;

  constructor() {
    const opParam = this.route.snapshot.paramMap.get('operation');
    if (!isKakoomaOperation(opParam)) {
      void this.router.navigate(['/sherlock']);
      this.operation = 'add';
    } else {
      this.operation = opParam;
    }
    this.engine = new KakoomaEngine(this.operation);
    this.progress = this.puzzleProgress.progressResource(this.engine.gameId);
    this.tierStats = this.puzzleProgress.tierStatsResource(this.engine.gameId);

    effect(() => {
      const value = this.progress.value();
      if (value && !this.initialized) {
        this.initialized = true;
        this.tier.set(value.current_tier);
        this.variationsCompleted.set(value.variations_completed);
        this.startNewPuzzle();
      }
    });
  }

  private startNewPuzzle(): void {
    this.puzzle.set(this.engine.generate(this.activeTier()));
    this.awaitingStart.set(true);
  }

  confirmStart(): void {
    if (!this.awaitingStart()) return;
    this.startedAt = Date.now();
    this.awaitingStart.set(false);
  }

  enterPractice(tier: PuzzleTier): void {
    if (tier === this.tier()) return;
    this.practiceTier.set(tier);
    this.practiceAttemptCount.set(0);
    this.startNewPuzzle();
  }

  exitPractice(): void {
    this.practiceTier.set(null);
    this.practiceAttemptCount.set(0);
    this.startNewPuzzle();
  }

  async select(index: number): Promise<void> {
    const puzzle = this.puzzle();
    if (!puzzle || !this.isAnswering()) return;

    const correct = this.engine.validate(puzzle, index);
    const startedAtIso = new Date(this.startedAt).toISOString();
    const completedAt = new Date();
    const timeTakenMs = completedAt.getTime() - this.startedAt;
    const practicing = this.practiceTier();

    this.feedback.set(correct ? 'correct' : 'incorrect');
    this.streak.set(correct ? this.streak() + 1 : 0);
    if (practicing) {
      this.practiceAttemptCount.update((v) => v + 1);
    }

    const previousFastest = practicing
      ? ((this.tierStats.value() ?? []).find((s) => s.tier === practicing)?.fastest_time_ms ?? null)
      : null;

    try {
      const result = await this.puzzleProgress.recordAttempt(this.engine.gameId, {
        started_at: startedAtIso,
        completed_at: completedAt.toISOString(),
        time_taken_ms: timeTakenMs,
        correct,
        practice_tier: practicing ?? undefined,
      });

      if (practicing) {
        if (correct && previousFastest !== null && timeTakenMs < previousFastest) {
          this.fasterMessage.set('Faster than before!');
        }
      } else {
        this.tier.set(result.progress.current_tier);
        this.variationsCompleted.set(result.progress.variations_completed);
        if (result.tier_advanced) {
          this.tierAdvancedMessage.set(`You unlocked ${tierLabel(result.progress.current_tier)}!`);
        }
      }
      this.tierStats.reload();
      this.storage.recordActivityToday();
    } catch {
      // Network hiccup — local feedback still shown; the next attempt retries.
    }

    setTimeout(() => {
      this.feedback.set(null);
      this.tierAdvancedMessage.set(null);
      this.fasterMessage.set(null);
      this.startNewPuzzle();
    }, FEEDBACK_DELAY_MS);
  }
}
