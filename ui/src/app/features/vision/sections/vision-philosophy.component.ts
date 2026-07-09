import { Component } from '@angular/core';
import { SketchComponent } from '../../../shared/components/sketch/sketch.component';
import { RevealOnScrollDirective } from '../../../shared/directives/reveal-on-scroll.directive';

@Component({
  selector: 'app-vision-philosophy',
  standalone: true,
  imports: [SketchComponent, RevealOnScrollDirective],
  template: `
    <section appRevealOnScroll class="mt-28 md:mt-36">
      <p class="font-mono text-xs uppercase tracking-widest text-muted" aria-hidden="true">III.</p>
      <h2 class="font-display text-2xl sm:text-3xl leading-snug text-ink mt-2">What we're actually building.</h2>

      <div class="relative mt-4">
        <app-sketch name="connecting-dots" [width]="48" [height]="48" class="text-navy hidden xl:block absolute -left-20 top-1" />
        <p class="font-sans text-lg leading-relaxed max-w-prose">
          Thinkingify isn't a curriculum and it isn't a productivity app. It's a small, quiet space for the
          parts of learning that don't show up on a test — noticing, questioning, sitting with an idea,
          changing your mind. Curiosity first. Confidence to ask "why" second. Everything else — puzzles,
          lessons, streaks — is scaffolding around those two things.
        </p>
      </div>

      <p class="font-display text-2xl sm:text-3xl text-moss mt-8">Curiosity. Confidence. Independence.</p>
    </section>
  `,
})
export class VisionPhilosophyComponent {}
