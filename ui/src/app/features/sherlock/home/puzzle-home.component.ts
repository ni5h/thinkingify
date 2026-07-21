import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PuzzleProgressService } from '../../../core/services/puzzle-progress.service';
import { isKakoomaGameId } from '../kakooma/kakooma.model';
import { formatTimePracticed, relativePracticeDate } from '../shared/puzzle-format.util';

@Component({
  selector: 'app-puzzle-home',
  standalone: true,
  imports: [RouterLink],
  template: `
    <h1 class="font-display text-3xl">Sherlock Holmes</h1>
    <p class="text-muted mt-2">Pick a game to play.</p>

    @if (roomStats().totalAttempts > 0) {
      <div class="flex flex-wrap gap-4 mt-6">
        <div class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
          <p class="text-xs text-muted font-mono">Puzzles attempted</p>
          <p class="font-display text-3xl text-ink mt-1">{{ roomStats().totalAttempts }}</p>
        </div>
        <div class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
          <p class="text-xs text-muted font-mono">This week</p>
          <p class="font-display text-3xl text-ink mt-1">{{ roomStats().attemptsThisWeek }}</p>
        </div>
      </div>
    }

    <h2 class="font-display text-xl mt-8">Games</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
      <a
        routerLink="/sherlock/kakooma"
        class="rounded-2xl border border-cloud bg-white shadow-sm p-5 hover:shadow-md transition-shadow"
      >
        <h3 class="font-display text-lg text-ink">Kakooma</h3>
        <p class="text-muted text-sm mt-1">Spot the hidden number in a group of numbers.</p>
        <p class="text-xs text-muted font-mono mt-3">
          {{ roomStats().totalAttempts }} attempts &middot; {{ timePracticedLabel() }} &middot; {{ lastPracticedLabel() }}
        </p>
      </a>
    </div>
  `,
})
export default class PuzzleHomeComponent {
  private readonly puzzleProgress = inject(PuzzleProgressService);

  readonly roomStats = this.puzzleProgress.roomStats(isKakoomaGameId);

  timePracticedLabel(): string {
    return formatTimePracticed(this.roomStats().totalTimeMs);
  }

  lastPracticedLabel(): string {
    return relativePracticeDate(this.roomStats().lastAttemptAt);
  }
}
