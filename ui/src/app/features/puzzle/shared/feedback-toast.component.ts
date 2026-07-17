import { Component, input } from '@angular/core';

export type FeedbackState = 'correct' | 'incorrect' | null;

@Component({
  selector: 'app-feedback-toast',
  standalone: true,
  template: `
    @if (state()) {
      <div
        class="absolute inset-0 flex items-center justify-center rounded-xl text-xl font-display pointer-events-none"
        [class]="state() === 'correct' ? 'bg-moss/10 text-moss-dark' : 'bg-amber/10 text-amber'"
      >
        {{ state() === 'correct' ? 'Correct!' : 'Try again' }}
      </div>
    }
  `,
})
export class FeedbackToastComponent {
  state = input<FeedbackState>(null);
}
