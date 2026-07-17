import { Component, computed, effect, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PuzzleProgressService } from '../../../core/services/puzzle-progress.service';
import { PuzzleTier, tierLabel } from '../../../core/models/puzzle';
import { FeedbackState } from '../shared/feedback-toast.component';
import { GameShellComponent } from '../shared/game-shell.component';
import { KakoomaEngine } from './kakooma.engine';
import { KakoomaPuzzle } from './kakooma.model';

const FEEDBACK_DELAY_MS = 1200;
const engine = new KakoomaEngine();

@Component({
  selector: 'app-kakooma',
  standalone: true,
  imports: [RouterLink, GameShellComponent],
  template: `
    <a routerLink="/puzzle" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
      &larr; Back to puzzles
    </a>

    <div class="mt-6">
      @if (puzzle(); as p) {
        <app-game-shell
          gameTitle="Kakooma"
          [tierLabel]="tierLabelText()"
          [variationsCompleted]="variationsCompleted()"
          [variationsPerTier]="10"
          [streak]="streak()"
          [running]="isAnswering()"
          [feedback]="feedback()"
        >
          <p class="text-center text-muted mb-6">
            Tap the number that's the {{ p.operation === 'add' ? 'sum' : 'product' }} of two others.
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
      }
    </div>
  `,
})
export default class KakoomaComponent {
  private readonly puzzleProgress = inject(PuzzleProgressService);
  private readonly progress = this.puzzleProgress.progressResource(engine.gameId);

  readonly tier = signal<PuzzleTier>('trial');
  readonly variationsCompleted = signal(0);
  readonly tierLabelText = computed(() => tierLabel(this.tier()));

  readonly streak = signal(0);
  readonly feedback = signal<FeedbackState>(null);
  readonly puzzle = signal<KakoomaPuzzle | null>(null);
  readonly tierAdvancedMessage = signal<string | null>(null);
  readonly isAnswering = computed(() => this.feedback() === null);

  private startedAt = 0;
  private initialized = false;

  constructor() {
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
    this.puzzle.set(engine.generate(this.tier()));
    this.startedAt = Date.now();
  }

  async select(index: number): Promise<void> {
    const puzzle = this.puzzle();
    if (!puzzle || !this.isAnswering()) return;

    const correct = engine.validate(puzzle, index);
    const startedAtIso = new Date(this.startedAt).toISOString();
    const completedAt = new Date();
    const timeTakenMs = completedAt.getTime() - this.startedAt;

    this.feedback.set(correct ? 'correct' : 'incorrect');
    this.streak.set(correct ? this.streak() + 1 : 0);

    try {
      const result = await this.puzzleProgress.recordAttempt(engine.gameId, {
        started_at: startedAtIso,
        completed_at: completedAt.toISOString(),
        time_taken_ms: timeTakenMs,
        correct,
      });
      this.tier.set(result.progress.current_tier);
      this.variationsCompleted.set(result.progress.variations_completed);
      if (result.tier_advanced) {
        this.tierAdvancedMessage.set(`You unlocked ${tierLabel(result.progress.current_tier)}!`);
      }
    } catch {
      // Network hiccup — local feedback still shown; the next attempt retries.
    }

    setTimeout(() => {
      this.feedback.set(null);
      this.tierAdvancedMessage.set(null);
      this.startNewPuzzle();
    }, FEEDBACK_DELAY_MS);
  }
}
