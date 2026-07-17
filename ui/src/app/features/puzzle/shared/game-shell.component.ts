import { Component, input } from '@angular/core';
import { TimerDisplayComponent } from './timer-display.component';
import { FeedbackState, FeedbackToastComponent } from './feedback-toast.component';

/**
 * Shared chrome for every drill game: title, timer, tier/streak indicator,
 * and a feedback overlay. Game-specific puzzle UI is projected via
 * <ng-content>.
 */
@Component({
  selector: 'app-game-shell',
  standalone: true,
  imports: [TimerDisplayComponent, FeedbackToastComponent],
  template: `
    <div class="rounded-2xl border border-cloud bg-white shadow-sm p-6 max-w-xl mx-auto">
      <header class="flex items-center justify-between mb-6">
        <h1 class="font-display text-xl text-ink">{{ gameTitle() }}</h1>
        <app-timer-display [running]="running()" />
      </header>

      <div class="flex items-center gap-4 mb-4 text-sm text-muted">
        <span>{{ tierLabel() }} &middot; {{ variationsCompleted() }}/{{ variationsPerTier() }}</span>
        <span>Streak: {{ streak() }}</span>
      </div>

      <div class="relative">
        <ng-content />
        <app-feedback-toast [state]="feedback()" />
      </div>
    </div>
  `,
})
export class GameShellComponent {
  gameTitle = input.required<string>();
  tierLabel = input.required<string>();
  variationsCompleted = input.required<number>();
  variationsPerTier = input(10);
  streak = input(0);
  running = input(false);
  feedback = input<FeedbackState>(null);
}
