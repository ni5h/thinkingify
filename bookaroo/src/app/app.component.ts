import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

// This is the frame that wraps every screen: the top bar and the footer stay,
// while the middle (<router-outlet>) swaps in whichever screen you're on.
@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: `
    <header class="border-b border-cloud bg-white/70 backdrop-blur">
      <div class="mx-auto max-w-4xl px-5 py-3 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="text-2xl">📚</span>
          <span class="font-display text-xl text-ink">Bookaroo</span>
        </div>
        <span class="font-mono text-xs text-muted">a Thinkingify product</span>
      </div>
    </header>

    <main class="mx-auto max-w-4xl px-5 pb-16 animate-slideUp">
      <router-outlet />
    </main>

    <footer class="border-t border-cloud">
      <div class="mx-auto max-w-4xl px-5 py-6 text-center">
        <p class="font-hand text-lg text-muted">Designed and built by Neo</p>
      </div>
    </footer>
  `,
})
export class AppComponent {}
