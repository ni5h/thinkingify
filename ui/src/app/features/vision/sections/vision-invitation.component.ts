import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { RevealOnScrollDirective } from '../../../shared/directives/reveal-on-scroll.directive';

@Component({
  selector: 'app-vision-invitation',
  standalone: true,
  imports: [RouterLink, RevealOnScrollDirective],
  template: `
    <section appRevealOnScroll class="mt-28 md:mt-36">
      <p class="font-mono text-xs uppercase tracking-widest text-muted" aria-hidden="true">V.</p>
      <h2 class="font-display text-3xl sm:text-4xl leading-snug text-ink mt-2">Begin, in your own words.</h2>
      <p class="font-sans text-lg leading-relaxed max-w-prose mt-4">
        Not a lesson. Not a prompt to get right. Just a page, and whatever's actually on your mind today.
      </p>

      <div class="flex flex-col sm:flex-row gap-4 sm:items-center mt-8">
        <a routerLink="/rowling" class="rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors">
          Begin your first page
        </a>
        <a routerLink="/blog" class="rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
          Or read what's already been written
        </a>
      </div>

      <div class="mt-16 mx-auto w-8 h-px bg-cloud" aria-hidden="true"></div>
    </section>
  `,
})
export class VisionInvitationComponent {}
