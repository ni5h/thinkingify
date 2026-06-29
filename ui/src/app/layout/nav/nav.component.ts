import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

interface NavItem {
  label: string;
  path: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Home', path: '/home' },
  { label: 'Puzzle', path: '/puzzle' },
  { label: 'Learn', path: '/learn' },
  { label: 'Journal', path: '/journal' },
  { label: 'Blog', path: '/blog' },
  { label: 'Progress', path: '/progress' },
];

@Component({
  selector: 'app-nav',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  template: `
    <!-- Desktop sidebar -->
    <nav class="hidden md:flex md:flex-col md:w-56 md:shrink-0 md:h-screen md:sticky md:top-0 border-r border-cloud bg-paper">
      <div class="px-6 py-8">
        <span class="font-display text-xl text-ink">Thinkingify</span>
      </div>
      <ul class="flex flex-col gap-1 px-3">
        @for (item of items; track item.path) {
          <li>
            <a
              [routerLink]="item.path"
              routerLinkActive="bg-cloud border-l-4 border-moss text-ink"
              class="block px-4 py-2 text-sm font-medium text-muted border-l-4 border-transparent hover:border-moss hover:text-ink transition-colors"
            >
              {{ item.label }}
            </a>
          </li>
        }
      </ul>
    </nav>

    <!-- Mobile bottom nav -->
    <nav class="md:hidden fixed bottom-0 left-0 right-0 border-t border-cloud bg-paper z-10">
      <ul class="flex justify-between">
        @for (item of items; track item.path) {
          <li class="flex-1">
            <a
              [routerLink]="item.path"
              routerLinkActive="text-moss border-t-2 border-moss"
              class="flex items-center justify-center py-3 text-xs font-medium text-muted border-t-2 border-transparent text-center"
            >
              {{ item.label }}
            </a>
          </li>
        }
      </ul>
    </nav>
  `,
})
export class NavComponent {
  readonly items = NAV_ITEMS;
}
