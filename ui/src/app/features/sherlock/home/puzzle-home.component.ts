import { Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PuzzleProgressService } from '../../../core/services/puzzle-progress.service';
import { GameStats, tierLabel } from '../../../core/models/puzzle';
import {
  KAKOOMA_OPERATIONS,
  KAKOOMA_OPERATION_DESCRIPTIONS,
  KAKOOMA_OPERATION_LABELS,
} from '../kakooma/kakooma.model';

interface OperationCard {
  operation: string;
  gameId: string;
  label: string;
  description: string;
  stats: GameStats | undefined;
}

function relativePracticeDate(iso: string | null): string {
  if (!iso) return 'Not started yet';
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / (1000 * 60 * 60 * 24));
  if (days <= 0) return 'Last practiced today';
  if (days === 1) return 'Last practiced yesterday';
  return `Last practiced ${days} days ago`;
}

@Component({
  selector: 'app-puzzle-home',
  standalone: true,
  imports: [RouterLink],
  template: `
    <h1 class="font-display text-3xl">Sherlock Holmes</h1>
    <p class="text-muted mt-2">Pick a game to play.</p>

    @if (roomTotalAttempts() > 0) {
      <p class="text-sm text-muted font-mono mt-2">{{ roomTotalAttempts() }} puzzles attempted so far</p>
    }

    <h2 class="font-display text-xl mt-8">Kakooma</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
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
export default class PuzzleHomeComponent {
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

  readonly roomTotalAttempts = computed(() =>
    this.cards().reduce((sum, c) => sum + (c.stats?.total_attempts ?? 0), 0)
  );

  tierLabelText(card: OperationCard): string {
    return tierLabel(card.stats?.current_tier ?? 'trial');
  }

  lastPracticed(card: OperationCard): string {
    return relativePracticeDate(card.stats?.last_attempt_at ?? null);
  }
}
