import { Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { RoomShellComponent, RoomDoor } from '../../shared/components/room-shell/room-shell.component';
import { MathService } from '../../core/services/math.service';

@Component({
  selector: 'app-ramanujan',
  standalone: true,
  imports: [RouterLink, RoomShellComponent],
  template: `
    <app-room-shell
      roomName="Ramanujan"
      subjectLabel="Maths · Class 4 CBSE"
      tone="ramanujan"
      icon="puzzle"
      [doors]="doors()"
    >
      <div chapters>
        <h2 class="text-sm font-medium text-muted">Problems</h2>
        @if (problems().length === 0) {
          <p class="text-sm text-muted mt-3">No problems yet &mdash; check back soon.</p>
        } @else {
          <ul class="mt-3 flex flex-col gap-2">
            @for (problem of problems(); track problem.id) {
              <li>
                <a
                  [routerLink]="['/ramanujan/problems', problem.slug]"
                  class="text-sm text-ink hover:text-moss transition-colors inline-flex items-baseline gap-2"
                >
                  {{ problem.title }}
                  <span class="text-xs text-muted font-mono">Lvl {{ problem.difficulty }}</span>
                </a>
              </li>
            }
          </ul>
        }
      </div>

      <p howItWorks class="text-sm text-muted max-w-prose">
        Pick a problem and think it through with your coach &mdash; who nudges your thinking but never
        just hands over the answer. No clock: slow down, spot the pattern, and crack it in your head.
      </p>
    </app-room-shell>
  `,
})
export default class RamanujanComponent {
  private readonly math = inject(MathService);
  readonly problems = computed(() => this.math.published() ?? []);

  readonly doors = computed<RoomDoor[]>(() => {
    const probs = this.problems();
    const doors: RoomDoor[] = [];
    // The card-session Learn flow (chapter → concept → cards → quick check).
    doors.push({
      id: 'learn',
      title: 'Learn',
      blurb: 'Short cards on one idea, then a few questions.',
      route: '/ramanujan/learn',
      icon: 'learn',
      recommended: true,
    });
    // Coached problem-solving — only shown once problems exist.
    if (probs.length > 0) {
      doors.push({
        id: 'problems',
        title: 'Coached problems',
        blurb: 'Work a problem through with your thinking coach.',
        route: ['/ramanujan/problems', probs[0].slug],
        icon: 'learn',
      });
    }
    doors.push({
      id: 'brothers',
      title: 'Brothers',
      blurb: 'Warm up: complements to 10, 100 and 1000.',
      route: '/ramanujan/brothers',
      icon: 'puzzle',
    });
    return doors;
  });
}
