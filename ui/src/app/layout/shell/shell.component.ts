import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { NavComponent } from '../nav/nav.component';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterOutlet, NavComponent],
  template: `
    <div class="flex min-h-screen bg-paper text-ink">
      <app-nav />
      <main class="flex-1 pb-20 md:pb-0">
        <div class="max-w-3xl mx-auto px-6 py-12 md:py-14 animate-slideUp">
          <router-outlet />
        </div>
      </main>
    </div>
  `,
})
export class ShellComponent {}
