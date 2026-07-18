import { Injectable, computed, inject } from '@angular/core';
import { StorageService } from './storage.service';
import { BlogService } from './blog.service';

const MS_PER_DAY = 24 * 60 * 60 * 1000;

function toDateOnly(iso: string): number {
  return new Date(iso + 'T00:00:00').getTime();
}

/** Longest run of consecutive calendar days within a sorted, deduped list of YYYY-MM-DD strings. */
function longestRun(sortedDates: string[]): number {
  if (sortedDates.length === 0) return 0;
  let best = 1;
  let current = 1;
  for (let i = 1; i < sortedDates.length; i++) {
    const gapDays = (toDateOnly(sortedDates[i]) - toDateOnly(sortedDates[i - 1])) / MS_PER_DAY;
    current = gapDays === 1 ? current + 1 : 1;
    best = Math.max(best, current);
  }
  return best;
}

/** Run of consecutive calendar days ending at the most recent date, counted back from today/yesterday. */
function currentRun(sortedDates: string[]): number {
  if (sortedDates.length === 0) return 0;
  const today = new Date().toISOString().slice(0, 10);
  const last = sortedDates[sortedDates.length - 1];
  const gapFromToday = (toDateOnly(today) - toDateOnly(last)) / MS_PER_DAY;
  // Streak is still "current" if the last activity was today or yesterday;
  // otherwise it has lapsed.
  if (gapFromToday > 1) return 0;

  let run = 1;
  for (let i = sortedDates.length - 1; i > 0; i--) {
    const gapDays = (toDateOnly(sortedDates[i]) - toDateOnly(sortedDates[i - 1])) / MS_PER_DAY;
    if (gapDays === 1) {
      run++;
    } else {
      break;
    }
  }
  return run;
}

/**
 * Exposes all progress/stat signals. Nothing here is persisted directly —
 * every value is computed() from raw activity in StorageService
 * (solvedPuzzleIds, completedLessonIds, activityDates) or, for
 * articlesWritten, from BlogService's Content resource.
 */
@Injectable({ providedIn: 'root' })
export class ProgressService {
  private readonly storage = inject(StorageService);
  private readonly blog = inject(BlogService);

  private readonly sortedActivityDates = computed(() =>
    [...this.storage.state().activityDates].sort()
  );

  // Counts published Content rows from BlogService's `all` resource, which
  // the backend already scopes to the current user's own posts for non-admin
  // roles (see content_service.list_all) — Rowling Room posts included.
  // Repurposed from a localStorage-only journalEntries count now that
  // Journal is retired (see ui/CLAUDE.md's Rooms IA section).
  readonly articlesWritten = computed(
    () => (this.blog.all() ?? []).filter((p) => p.status === 'published').length
  );

  readonly puzzlesSolvedCount = computed(() => this.storage.state().solvedPuzzleIds.length);

  readonly lessonsCompletedCount = computed(() => this.storage.state().completedLessonIds.length);

  readonly currentStreak = computed(() => currentRun(this.sortedActivityDates()));

  readonly longestStreak = computed(() => longestRun(this.sortedActivityDates()));

  readonly totalDaysLearned = computed(() => this.sortedActivityDates().length);

  readonly lastActiveDate = computed(() => {
    const dates = this.sortedActivityDates();
    return dates.length > 0 ? dates[dates.length - 1] : null;
  });
}
