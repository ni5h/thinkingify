import { Component, OnDestroy, computed, effect, input, signal } from '@angular/core';

const TICK_MS = 100;

/**
 * Purely cosmetic stopwatch — ticks up while `running` is true, resets on
 * false->true. The real scoring clock is Date.now() captured directly in
 * the game component (see kakooma.component.ts); this just gives the
 * learner a sense that time is being measured.
 */
@Component({
  selector: 'app-timer-display',
  standalone: true,
  template: `<span class="font-mono text-sm text-muted">{{ display() }}</span>`,
})
export class TimerDisplayComponent implements OnDestroy {
  running = input(false);

  private readonly elapsedMs = signal(0);
  private intervalId: ReturnType<typeof setInterval> | null = null;

  readonly display = computed(() => `${(this.elapsedMs() / 1000).toFixed(1)}s`);

  constructor() {
    effect(() => {
      if (this.running()) {
        this.elapsedMs.set(0);
        this.intervalId = setInterval(() => this.elapsedMs.update((v) => v + TICK_MS), TICK_MS);
      } else {
        this.clearTimer();
      }
    });
  }

  ngOnDestroy(): void {
    this.clearTimer();
  }

  private clearTimer(): void {
    if (this.intervalId !== null) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }
}
