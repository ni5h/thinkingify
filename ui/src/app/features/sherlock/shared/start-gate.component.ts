import { Component, input, output } from '@angular/core';

/**
 * Blurred "tap to start" overlay shown before every round — the scoring
 * clock only starts once dismissed, so a learner isn't penalized for not
 * being ready the instant a puzzle is generated. Mounted the same way as
 * FeedbackToastComponent (absolute inset-0 inside game-shell's relative
 * wrapper), but pointer-events stay enabled since this is a tap target.
 */
@Component({
  selector: 'app-start-gate',
  standalone: true,
  template: `
    @if (visible()) {
      <div
        class="absolute inset-0 flex flex-col items-center justify-center gap-3 rounded-xl bg-white/70 backdrop-blur-md cursor-pointer text-center px-4"
        role="button"
        tabindex="0"
        (click)="start.emit()"
        (keydown.enter)="start.emit()"
        (keydown.space)="start.emit()"
      >
        <span class="rounded-xl bg-moss px-6 py-2.5 text-white text-sm font-medium shadow-sm">
          Tap to start
        </span>
      </div>
    }
  `,
})
export class StartGateComponent {
  visible = input(false);
  start = output<void>();
}
