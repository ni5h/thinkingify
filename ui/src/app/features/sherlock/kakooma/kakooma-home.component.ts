import { Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PuzzleProgressService } from '../../../core/services/puzzle-progress.service';
import { GameStats, tierLabel } from '../../../core/models/puzzle';
import { relativePracticeDate } from '../shared/puzzle-format.util';
import { KAKOOMA_OPERATIONS, KAKOOMA_OPERATION_DESCRIPTIONS, KAKOOMA_OPERATION_LABELS } from './kakooma.model';

interface OperationCard {
  operation: string;
  gameId: string;
  label: string;
  description: string;
  stats: GameStats | undefined;
}

@Component({
  selector: 'app-kakooma-home',
  standalone: true,
  imports: [RouterLink],
  template: `
    <a routerLink="/sherlock" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
      &larr; Back to puzzles
    </a>

    <h1 class="font-display text-3xl mt-4">Kakooma</h1>
    <p class="text-muted mt-2">Spot the hidden number in a group of numbers. Pick an operation.</p>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6">
      @for (card of cards(); track card.gameId) {
        <a
          [routerLink]="['/sherlock/kakooma', card.operation]"
          class="rounded-2xl border border-cloud bg-white shadow-sm p-5 hover:shadow-md transition-shadow"
        >
          <div class="flex items-baseline justify-between gap-2">
            <h3 class="font-display text-lg text-ink">{{ card.label }}</h3>
            <span class="text-xs font-mono text-moss-dark bg-moss/10 rounded-lg px-2 py-0.5">
              {{ tierLabelText(card) }}
            </span>
          </div>
          <p class="text-muted text-sm mt-1">{{ card.description }}</p>
          <p class="text-xs text-muted font-mono mt-3">
            {{ card.stats?.total_attempts ?? 0 }} attempts &middot; {{ lastPracticed(card) }}
          </p>
        </a>
      }
    </div>
  `,
})
export default class KakoomaHomeComponent {
  private readonly puzzleProgress = inject(PuzzleProgressService);

  private readonly statsByGameId = computed(() => {
    const map = new Map<string, GameStats>();
    for (const s of this.puzzleProgress.stats() ?? []) map.set(s.game_id, s);
    return map;
  });

  readonly cards = computed<OperationCard[]>(() =>
    KAKOOMA_OPERATIONS.map((operation) => {
      const gameId = `kakooma-${operation}`;
      return {
        operation,
        gameId,
        label: KAKOOMA_OPERATION_LABELS[operation],
        description: KAKOOMA_OPERATION_DESCRIPTIONS[operation],
        stats: this.statsByGameId().get(gameId),
      };
    })
  );

  tierLabelText(card: OperationCard): string {
    return tierLabel(card.stats?.current_tier ?? 'trial');
  }

  lastPracticed(card: OperationCard): string {
    return relativePracticeDate(card.stats?.last_attempt_at ?? null);
  }
}
