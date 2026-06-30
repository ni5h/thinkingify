import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { IconComponent, IconName } from '../../shared/components/icon/icon.component';

interface ModuleCard {
  label: string;
  path: string;
  icon: IconName;
  description: string;
}

const MODULES: ModuleCard[] = [
  { label: 'Home', path: '/home', icon: 'home', description: 'A daily check-in: a streak, today’s puzzle and lesson, a peek at your journal.' },
  { label: 'Puzzle', path: '/puzzle', icon: 'puzzle', description: 'One puzzle at a time, with a hint if you get stuck. No timers, no pressure.' },
  { label: 'Learn', path: '/learn', icon: 'learn', description: 'A short lesson each day, ending with a prompt to close the laptop and think.' },
  { label: 'Journal', path: '/journal', icon: 'journal', description: 'A notebook page for reflecting in your own words — plain and unhurried.' },
  { label: 'Blog', path: '/blog', icon: 'blog', description: 'Your own publishing space, for writing things worth sharing.' },
  { label: 'Progress', path: '/progress', icon: 'progress', description: 'A plain record of what you’ve done — no leaderboards, no comparisons.' },
];

@Component({
  selector: 'app-vision',
  standalone: true,
  imports: [RouterLink, IconComponent],
  template: `
    <section class="text-center max-w-xl mx-auto mt-6">
      <h1 class="font-display text-4xl text-ink">Thinkingify</h1>
      <p class="text-muted text-lg mt-3">
        Technology that asks you to think, not just to tap.
      </p>
      <a
        routerLink="/home"
        class="inline-block mt-6 rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors"
      >
        Go to dashboard
      </a>
    </section>

    <section class="max-w-xl mx-auto mt-14">
      <p class="text-ink leading-relaxed">
        Most apps compete for attention. Thinkingify does the opposite: every
        screen is built to end, not to keep you scrolling. A puzzle to solve,
        a short lesson, a few minutes to write down what you actually think
        &mdash; then you put the device down. Less screen time, more thinking
        time. That's the whole idea.
      </p>
    </section>

    <section class="mt-14">
      <h2 class="font-display text-2xl text-ink text-center">What's inside</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6">
        @for (module of modules; track module.path) {
          <a
            [routerLink]="module.path"
            class="rounded-2xl border border-cloud bg-white shadow-sm p-5 hover:shadow-md transition-shadow"
          >
            <app-icon [name]="module.icon" [size]="24" class="text-moss" />
            <h3 class="font-display text-lg text-ink mt-3">{{ module.label }}</h3>
            <p class="text-muted text-sm mt-1">{{ module.description }}</p>
          </a>
        }
      </div>
    </section>
  `,
})
export default class VisionComponent {
  readonly modules = MODULES;
}
