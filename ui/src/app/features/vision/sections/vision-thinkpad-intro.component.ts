import { Component } from '@angular/core';
import { RevealOnScrollDirective } from '../../../shared/directives/reveal-on-scroll.directive';

@Component({
  selector: 'app-vision-thinkpad-intro',
  standalone: true,
  imports: [RevealOnScrollDirective],
  template: `
    <section appRevealOnScroll class="mt-28 md:mt-36">
      <p class="font-mono text-xs uppercase tracking-widest text-muted" aria-hidden="true">IV.</p>
      <h2 class="font-display text-2xl sm:text-3xl leading-snug text-ink mt-2">Someday, a place called ThinkPad.</h2>
      <p class="font-sans text-lg leading-relaxed max-w-prose mt-4">
        The long-term idea has a name: ThinkPad — one place to write, reflect, answer a real question, and
        follow an idea somewhere unexpected, with a companion that asks rather than answers. It doesn't
        exist yet. What exists today is smaller, and already does a version of the same thing: a page to
        write on, and a habit of showing up to it.
      </p>
    </section>
  `,
})
export class VisionThinkpadIntroComponent {}
