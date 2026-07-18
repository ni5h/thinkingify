import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-puzzle-home',
  standalone: true,
  imports: [RouterLink],
  template: `
    <h1 class="font-display text-3xl">Puzzles</h1>
    <p class="text-muted mt-2">Pick a game to play.</p>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-8">
      <a
        routerLink="/puzzle/kakooma"
        class="rounded-2xl border border-cloud bg-white shadow-sm p-5 hover:shadow-md transition-shadow"
      >
        <h2 class="font-display text-lg text-ink">Kakooma</h2>
        <p class="text-muted text-sm mt-1">Spot the sum or product hiding in a group of numbers.</p>
      </a>
    </div>
  `,
})
export default class PuzzleHomeComponent {}
