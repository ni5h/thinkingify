import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { IconComponent } from '../../shared/components/icon/icon.component';
import { MathService } from '../../core/services/math.service';

@Component({
  selector: 'app-ramanujan',
  standalone: true,
  imports: [RouterLink, IconComponent],
  template: `
    <div class="flex items-start gap-4">
      <app-icon name="puzzle" [size]="32" class="text-moss shrink-0 mt-1" />
      <div>
        <h1 class="font-display text-3xl">Ramanujan</h1>
        <p class="text-muted mt-2 max-w-prose">
          Ramanujan taught himself maths from an old book and filled notebooks with patterns
          nobody had seen before. In this room you don't race a clock &mdash; you slow down, spot
          patterns, and figure things out in your head. Pick a problem, think it through with your
          coach (who'll never just tell you the answer), and see if you can crack it.
        </p>
      </div>
    </div>

    <h2 class="font-display text-xl mt-10">Practice</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
      <a
        routerLink="/ramanujan/brothers"
        class="rounded-2xl border border-amber/40 bg-amber/5 shadow-sm p-5 hover:shadow-md transition-shadow flex items-center justify-between gap-3"
      >
        <div>
          <h3 class="font-display text-lg text-ink">Brothers</h3>
          <p class="text-sm text-muted mt-1">Complements to 10, 100, 1000 &mdash; the heart of mental maths.</p>
        </div>
        <app-icon name="arrow-right" [size]="20" class="text-amber shrink-0" />
      </a>
    </div>

    <h2 class="font-display text-xl mt-10">Problems</h2>
    @if ((problems() ?? []).length === 0) {
      <p class="text-muted mt-4">No problems yet &mdash; check back soon.</p>
    } @else {
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
        @for (problem of problems(); track problem.id) {
          <a
            [routerLink]="['/ramanujan/problems', problem.slug]"
            class="rounded-2xl border border-cloud bg-white shadow-sm p-5 hover:shadow-md transition-shadow flex flex-col gap-2"
          >
            <div class="flex items-start justify-between gap-3">
              <h3 class="font-display text-lg text-ink">{{ problem.title }}</h3>
              <span class="text-xs text-muted font-mono shrink-0 mt-1">Level {{ problem.difficulty }}</span>
            </div>
            @if (problem.concept_tags.length > 0) {
              <div class="flex flex-wrap gap-1.5">
                @for (tag of problem.concept_tags; track tag) {
                  <span class="rounded-lg bg-cloud/60 px-2 py-0.5 text-xs text-muted">{{ tag }}</span>
                }
              </div>
            }
          </a>
        }
      </div>
    }
  `,
})
export default class RamanujanComponent {
  private readonly math = inject(MathService);
  readonly problems = this.math.published;
}
