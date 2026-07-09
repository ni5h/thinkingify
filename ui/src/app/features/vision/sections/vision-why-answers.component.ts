import { Component } from '@angular/core';
import { SketchComponent } from '../../../shared/components/sketch/sketch.component';
import { RevealOnScrollDirective } from '../../../shared/directives/reveal-on-scroll.directive';

@Component({
  selector: 'app-vision-why-answers',
  standalone: true,
  imports: [SketchComponent, RevealOnScrollDirective],
  template: `
    <section appRevealOnScroll class="mt-28 md:mt-36">
      <p class="font-mono text-xs uppercase tracking-widest text-muted" aria-hidden="true">I.</p>
      <h2 class="font-display text-2xl sm:text-3xl leading-snug text-ink mt-2">Most of school is answers.</h2>
      <p class="font-sans text-lg leading-relaxed max-w-prose mt-4">
        Right answers are easy to grade and hard to argue with. So that's what gets taught, tested, and
        rewarded — a right answer, found quickly, written neatly. Somewhere in that process the question
        gets lost. Nobody asks why the answer is right, or what would have to be true for it to be wrong.
      </p>

      <div class="relative mt-8">
        <app-sketch name="bracket" [width]="20" [height]="100" class="text-navy hidden xl:block absolute -left-16 top-0" />
        <p class="font-display text-xl sm:text-2xl italic leading-snug max-w-prose">
          A child who can recite the answer isn't the same as a child who knows how they'd find it again.
        </p>
      </div>
    </section>
  `,
})
export class VisionWhyAnswersComponent {}
