import { Component } from '@angular/core';
import { IconComponent } from '../../shared/components/icon/icon.component';

@Component({
  selector: 'app-puzzle',
  standalone: true,
  imports: [IconComponent],
  template: `
    <div class="rounded-2xl border border-cloud bg-white shadow-sm p-10 text-center max-w-md mx-auto mt-6">
      <app-icon name="puzzle" [size]="40" class="mx-auto text-moss/50" />
      <h1 class="font-display text-3xl mt-4">Puzzle</h1>
      <p class="text-muted mt-2">Phase 3 builds the puzzle module here.</p>
    </div>
  `,
})
export default class PuzzleComponent {}
