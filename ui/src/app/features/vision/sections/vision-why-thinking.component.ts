import { Component } from '@angular/core';
import { RevealOnScrollDirective } from '../../../shared/directives/reveal-on-scroll.directive';
import { SocraticWidgetComponent } from '../components/socratic-widget.component';

@Component({
  selector: 'app-vision-why-thinking',
  standalone: true,
  imports: [RevealOnScrollDirective, SocraticWidgetComponent],
  template: `
    <section appRevealOnScroll class="mt-28 md:mt-36">
      <p class="font-mono text-xs uppercase tracking-widest text-muted" aria-hidden="true">II.</p>
      <h2 class="font-display text-2xl sm:text-3xl leading-snug text-ink mt-2">Thinking is a habit, not a subject.</h2>
      <p class="font-sans text-lg leading-relaxed max-w-prose mt-4">
        You don't get better at thinking by being told what's true. You get better by asking a slightly
        harder question than the one you started with — out loud, on paper, or just in your head — and
        sitting with it for a moment before moving on. It looks like this.
      </p>

      <div class="mt-10">
        <app-socratic-widget />
      </div>

      <p class="font-sans text-base text-muted italic mt-6">There's rarely a right answer here. That's the point.</p>
    </section>
  `,
})
export class VisionWhyThinkingComponent {}
