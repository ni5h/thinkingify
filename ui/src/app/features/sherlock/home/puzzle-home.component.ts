import { Component, inject } from '@angular/core';
import { PuzzleProgressService } from '../../../core/services/puzzle-progress.service';
import { isKakoomaGameId } from '../kakooma/kakooma.model';
import { formatTimePracticed, relativePracticeDate } from '../shared/puzzle-format.util';
import { RoomShellComponent, RoomDoor } from '../../../shared/components/room-shell/room-shell.component';

@Component({
  selector: 'app-puzzle-home',
  standalone: true,
  imports: [RoomShellComponent],
  template: `
    <app-room-shell
      roomName="Sherlock Holmes"
      subjectLabel="Puzzles & reasoning"
      tone="sherlock"
      icon="sherlock"
      [doors]="doors"
    >
      <div chapters>
        @if (roomStats().totalAttempts > 0) {
          <h2 class="text-sm font-medium text-muted">Your practice</h2>
          <dl class="mt-3 grid grid-cols-2 gap-3">
            <div class="rounded-xl border border-cloud bg-white p-3">
              <dt class="text-xs text-muted font-mono">Attempts</dt>
              <dd class="font-display text-2xl text-ink mt-0.5">{{ roomStats().totalAttempts }}</dd>
            </div>
            <div class="rounded-xl border border-cloud bg-white p-3">
              <dt class="text-xs text-muted font-mono">This week</dt>
              <dd class="font-display text-2xl text-ink mt-0.5">{{ roomStats().attemptsThisWeek }}</dd>
            </div>
          </dl>
          <p class="text-xs text-muted font-mono mt-3">
            {{ timePracticedLabel() }} &middot; {{ lastPracticedLabel() }}
          </p>
        } @else {
          <p class="text-sm text-muted">Pick a game to start — no clock, no score.</p>
        }
      </div>

      <p howItWorks class="text-sm text-muted max-w-prose">
        Warm up your reasoning with short, pressure-free puzzles. These sharpen the thinking you'll
        use to crack the harder questions in the other rooms.
      </p>
    </app-room-shell>
  `,
})
export default class PuzzleHomeComponent {
  private readonly puzzleProgress = inject(PuzzleProgressService);

  readonly roomStats = this.puzzleProgress.roomStats(isKakoomaGameId);

  readonly doors: RoomDoor[] = [
    {
      id: 'kakooma',
      title: 'Kakooma',
      blurb: 'Spot the hidden number in a group of numbers.',
      route: '/sherlock/kakooma',
      icon: 'puzzle',
      recommended: true,
    },
  ];

  timePracticedLabel(): string {
    return formatTimePracticed(this.roomStats().totalTimeMs);
  }

  lastPracticedLabel(): string {
    return relativePracticeDate(this.roomStats().lastAttemptAt);
  }
}
