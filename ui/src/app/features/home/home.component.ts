import { Component, computed, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ProgressService } from '../../core/services/progress.service';
import { JournalService } from '../../core/services/journal.service';

const CHILD_NAME = 'Neo';

function greetingForHour(hour: number): string {
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    <h1 class="font-display text-3xl">{{ greeting }}, {{ childName }}.</h1>

    <div class="flex gap-8 mt-6">
      <div>
        <p class="font-mono text-3xl text-moss-dark">{{ progress.currentStreak() }}</p>
        <p class="text-xs text-muted mt-1">day streak</p>
      </div>
      <div>
        <p class="font-mono text-3xl text-ink">{{ progress.longestStreak() }}</p>
        <p class="text-xs text-muted mt-1">longest streak</p>
      </div>
      <div>
        <p class="font-mono text-3xl text-ink">{{ progress.totalDaysLearned() }}</p>
        <p class="text-xs text-muted mt-1">days learned</p>
      </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-10">
      <a
        routerLink="/puzzle"
        class="block bg-white border border-cloud border-l-4 border-l-transparent hover:border-l-moss p-5 transition-colors"
      >
        <h2 class="font-display text-xl text-ink">Today's Puzzle</h2>
        <p class="text-muted text-sm mt-1">Stretch your thinking with one puzzle.</p>
      </a>
      <a
        routerLink="/learn"
        class="block bg-white border border-cloud border-l-4 border-l-transparent hover:border-l-moss p-5 transition-colors"
      >
        <h2 class="font-display text-xl text-ink">Today's Lesson</h2>
        <p class="text-muted text-sm mt-1">Learn one new thing, then pause and think.</p>
      </a>
    </div>

    <div class="mt-10">
      <div class="flex items-baseline justify-between gap-4">
        <h2 class="font-display text-xl text-ink">Journal</h2>
        <a routerLink="/journal" class="text-sm text-muted hover:text-ink border-b border-transparent hover:border-ink">
          {{ latestEntry() ? 'See all' : 'Write your first entry' }}
        </a>
      </div>

      @if (latestEntry()) {
        <div class="border border-cloud p-5 mt-3">
          <p class="font-display text-lg text-ink">{{ latestEntry()!.title || '(untitled)' }}</p>
          <p class="text-xs text-muted font-mono mt-1">{{ latestEntry()!.date | date: 'mediumDate' }}</p>
          <p class="text-muted text-sm mt-3">{{ latestEntry()!.whatILearned }}</p>
        </div>
      } @else {
        <p class="text-muted mt-3">No entries yet. Today's a good day to start.</p>
      }
    </div>
  `,
})
export default class HomeComponent {
  readonly progress = inject(ProgressService);
  private readonly journal = inject(JournalService);

  readonly childName = CHILD_NAME;
  readonly greeting = greetingForHour(new Date().getHours());

  readonly latestEntry = computed(() => this.journal.entries()[0]);
}
