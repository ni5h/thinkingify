import { Component, computed } from '@angular/core';
import { RoomDoor, RoomShellComponent } from '../../shared/components/room-shell/room-shell.component';

@Component({
  selector: 'app-einstein',
  standalone: true,
  imports: [RoomShellComponent],
  template: `
    <app-room-shell
      roomName="Einstein"
      subjectLabel="Science & EVS · Class 4 CBSE"
      tone="einstein"
      icon="learn"
      [doors]="doors()"
    >
      <div chapters>
        <h2 class="text-sm font-medium text-muted">Chapters</h2>
        <p class="text-sm text-muted mt-3">Open Learn to see your chapters.</p>
      </div>

      <p howItWorks class="text-sm text-muted max-w-prose">
        Short cards on one idea at a time, each with a picture and a question to think about &mdash;
        then a few quick questions to check it stuck. No clock, no score.
      </p>
    </app-room-shell>
  `,
})
export default class EinsteinComponent {
  readonly doors = computed<RoomDoor[]>(() => [
    {
      id: 'learn',
      title: 'Learn',
      blurb: 'Short cards on one idea, then a few questions.',
      route: '/einstein/learn',
      icon: 'learn',
      recommended: true,
    },
  ]);
}
