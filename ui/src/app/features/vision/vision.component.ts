import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

/**
 * Parent landing page at `/` for the Class 4 pilot. The CTA points at the
 * existing sign-in for now; Phase 6 replaces it with parent-first sign-up.
 * Copy is intentionally free of outcome claims (no "guaranteed", "rank",
 * "toppers").
 */
@Component({
  selector: 'app-vision',
  standalone: true,
  imports: [RouterLink],
  template: `
    <!-- Hero -->
    <section>
      <p class="text-xs font-semibold tracking-widest text-moss">CBSE CLASS 4 · MATHS &amp; EVS · OLYMPIAD THINKING</p>
      <h1 class="font-display text-3xl sm:text-4xl text-ink mt-3 leading-tight">
        Prepare for CBSE. Think like an olympiad champion.
      </h1>
      <p class="text-muted mt-4 max-w-prose text-lg">
        Thinkingify helps your child understand each chapter, explain it in their own words, and take
        on olympiad-style puzzles, so they learn to crack the hard questions themselves.
      </p>
      <a routerLink="/studio/login" class="inline-block mt-6 rounded-xl bg-moss px-6 py-3 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors">
        Join the Class 4 pilot
      </a>
    </section>

    <!-- Dark band: how a concept sticks -->
    <section class="mt-14 rounded-2xl bg-ink text-white p-8">
      <h2 class="font-display text-xl">How a concept sticks</h2>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-5 mt-6">
        @for (step of flow; track step.label; let i = $index) {
          <div>
            <p class="font-display text-amber text-lg">{{ i + 1 }}</p>
            <p class="font-medium mt-1">{{ step.label }}</p>
            <p class="text-sm text-white/60 mt-1">{{ step.blurb }}</p>
          </div>
        }
      </div>
    </section>

    <!-- Value cards -->
    <section class="mt-14 grid grid-cols-1 sm:grid-cols-3 gap-4">
      @for (v of values; track v.title) {
        <div class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
          <h3 class="font-display text-lg text-ink">{{ v.title }}</h3>
          <p class="text-sm text-muted mt-2">{{ v.blurb }}</p>
        </div>
      }
    </section>

    <!-- Our promises -->
    <section class="mt-14">
      <h2 class="font-display text-xl text-ink">Our promises</h2>
      <ul class="mt-4 flex flex-col gap-3">
        @for (promise of promises; track promise) {
          <li class="flex items-start gap-3">
            <span class="text-moss font-semibold mt-0.5" aria-hidden="true">&check;</span>
            <span class="text-muted">{{ promise }}</span>
          </li>
        }
      </ul>
    </section>

    <!-- Pilot section + CTA -->
    <section class="mt-14 rounded-2xl border border-moss/30 bg-moss/5 p-8 text-center">
      <h2 class="font-display text-2xl text-ink">A small pilot for Class 4 families</h2>
      <p class="text-muted mt-2 max-w-prose mx-auto">
        We're running a short pilot with a handful of families around Class 4 Maths and EVS. If that's
        your child, come try it and tell us what helps.
      </p>
      <a routerLink="/studio/login" class="inline-block mt-5 rounded-xl bg-moss px-6 py-3 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors">
        Join the Class 4 pilot
      </a>
    </section>
  `,
})
export default class VisionComponent {
  readonly flow = [
    { label: 'Listen', blurb: 'A short audio on one idea.' },
    { label: 'Write', blurb: 'Explain it in their own words.' },
    { label: 'Solve', blurb: 'A few questions to apply it.' },
    { label: 'Recall', blurb: 'Write it from memory, days later.' },
  ];

  readonly values = [
    { title: 'Every CBSE chapter', blurb: 'Maths and EVS for Class 4, matched to your child’s textbook chapters.' },
    { title: 'Olympiad-style thinking', blurb: 'Puzzles that grow the reasoning behind the hard questions — no timer, no rank.' },
    { title: 'A weekly report that tells you something', blurb: 'What’s solid, what needs another look, and one thing to talk about at dinner.' },
  ];

  readonly promises = [
    'No leaderboards, ranks or streaks.',
    'No ads, and we never sell your data.',
    'Mistakes are investigation, not penalty.',
    'Parents consent first — and can see and delete everything.',
  ];
}
