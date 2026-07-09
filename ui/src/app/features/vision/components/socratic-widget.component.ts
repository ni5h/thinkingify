import { Component, computed, signal } from '@angular/core';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { SketchComponent } from '../../../shared/components/sketch/sketch.component';

const CHAINS: string[][] = [
  [
    'Is the Earth round?',
    'How do you know?',
    'What evidence convinced you?',
    'Would you still believe it if everyone around you said it was flat?',
  ],
  [
    'Is it fair that the oldest kid always goes first?',
    'Who decided that rule?',
    'Was there a good reason, or just habit?',
    'What would you have to see happen to change your mind?',
  ],
  [
    'Why does the moon seem to follow the car?',
    'Is it actually moving, or does it just look that way?',
    "What's the difference between what you see and what's true?",
    "Can you think of something else that looks true but isn't?",
  ],
];

@Component({
  selector: 'app-socratic-widget',
  standalone: true,
  imports: [IconComponent, SketchComponent],
  template: `
    <div class="relative rounded-2xl border border-cloud bg-white shadow-sm p-8">
      <app-sketch name="margin-arrow" [width]="60" [height]="40" class="text-navy hidden xl:block absolute -right-20 top-8" />

      @if (pastQuestions().length > 0) {
        <ul class="flex flex-col gap-3 mb-5 border-l-2 border-cloud pl-4">
          @for (question of pastQuestions(); track question) {
            <li class="font-sans text-sm text-muted leading-relaxed">{{ question }}</li>
          }
        </ul>
      }

      <p class="font-display text-xl sm:text-2xl text-ink leading-snug" aria-live="polite">
        {{ currentQuestion() }}
      </p>

      <button
        type="button"
        (click)="advance()"
        class="group mt-6 inline-flex items-center gap-2 text-sm font-medium text-moss underline decoration-moss/30 underline-offset-4 hover:decoration-moss transition-colors focus-visible:outline-2 focus-visible:outline-moss focus-visible:outline-offset-2 rounded-sm"
      >
        {{ isLastStep() ? 'Try another question' : 'Click to think further' }}
        <app-icon name="arrow-right" [size]="14" class="transition-transform group-hover:translate-x-0.5" />
      </button>
    </div>
  `,
})
export class SocraticWidgetComponent {
  private readonly chains = CHAINS;
  private readonly chainIndex = signal(0);
  private readonly step = signal(0);

  private readonly revealed = computed(() => this.chains[this.chainIndex()].slice(0, this.step() + 1));

  readonly pastQuestions = computed(() => this.revealed().slice(0, -1));
  readonly currentQuestion = computed(() => this.revealed().at(-1)!);
  readonly isLastStep = computed(() => this.step() === this.chains[this.chainIndex()].length - 1);

  advance(): void {
    if (this.isLastStep()) {
      this.chainIndex.update((i) => (i + 1) % this.chains.length);
      this.step.set(0);
    } else {
      this.step.update((s) => s + 1);
    }
  }
}
