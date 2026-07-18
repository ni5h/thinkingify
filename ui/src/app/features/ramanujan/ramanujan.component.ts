import { Component } from '@angular/core';
import { IconComponent } from '../../shared/components/icon/icon.component';

@Component({
  selector: 'app-ramanujan',
  standalone: true,
  imports: [IconComponent],
  template: `
    <div class="rounded-2xl border border-cloud bg-white shadow-sm p-10 text-center max-w-md mx-auto mt-6">
      <app-icon name="puzzle" [size]="40" class="mx-auto text-moss/50" />
      <h1 class="font-display text-3xl mt-4">Ramanujan</h1>
      <p class="text-muted mt-2">The Maths room &mdash; content and flow not designed yet.</p>
    </div>
  `,
})
export default class RamanujanComponent {}
