import { Component, signal } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { IconComponent, IconName } from '../../shared/components/icon/icon.component';

interface NavItem {
  label: string;
  path: string;
  icon: IconName;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Home', path: '/home', icon: 'home' },
  { label: 'Puzzle', path: '/puzzle', icon: 'puzzle' },
  { label: 'Learn', path: '/learn', icon: 'learn' },
  { label: 'Journal', path: '/journal', icon: 'journal' },
  { label: 'Blog', path: '/blog', icon: 'blog' },
  { label: 'Progress', path: '/progress', icon: 'progress' },
];

@Component({
  selector: 'app-nav',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, IconComponent],
  template: `
    <!-- Desktop sidebar -->
    <nav [class]="sidebarClass()">
      <div class="flex items-center gap-3 px-4 py-9">
        <button
          type="button"
          (click)="collapsed.set(!collapsed())"
          [attr.aria-label]="collapsed() ? 'Expand navigation' : 'Collapse navigation'"
          class="shrink-0 rounded-lg p-2 text-muted hover:bg-cloud/60 hover:text-ink transition-colors"
        >
          <app-icon name="menu" [size]="20" />
        </button>
        @if (!collapsed()) {
          <a routerLink="/" class="font-display text-xl text-ink hover:text-moss transition-colors">Thinkingify</a>
        }
      </div>
      <ul class="flex flex-col gap-1.5 px-3">
        @for (item of items; track item.path) {
          <li>
            <a
              [routerLink]="item.path"
              [attr.title]="collapsed() ? item.label : null"
              routerLinkActive="bg-moss/10 border-l-4 border-moss text-ink rounded-r-xl"
              [class]="linkClass()"
            >
              <app-icon [name]="item.icon" [size]="20" />
              @if (!collapsed()) {
                <span>{{ item.label }}</span>
              }
            </a>
          </li>
        }
      </ul>
    </nav>

    <!-- Mobile bottom nav -->
    <nav class="md:hidden fixed bottom-0 left-0 right-0 border-t border-cloud bg-paper z-10 shadow-[0_-2px_8px_rgba(28,25,23,0.06)]">
      <ul class="flex justify-between">
        @for (item of items; track item.path) {
          <li class="flex-1">
            <a
              [routerLink]="item.path"
              routerLinkActive="text-moss border-t-2 border-moss"
              class="flex flex-col items-center justify-center gap-0.5 py-2.5 text-[11px] font-medium text-muted border-t-2 border-transparent text-center transition-colors"
            >
              <app-icon [name]="item.icon" [size]="20" />
              <span>{{ item.label }}</span>
            </a>
          </li>
        }
      </ul>
    </nav>
  `,
})
export class NavComponent {
  readonly items = NAV_ITEMS;
  readonly collapsed = signal(false);

  sidebarClass(): string {
    const width = this.collapsed() ? 'md:w-20' : 'md:w-60';
    return `hidden md:flex md:flex-col ${width} md:shrink-0 md:h-screen md:sticky md:top-0 border-r border-cloud bg-paper transition-[width] duration-200`;
  }

  linkClass(): string {
    return this.collapsed()
      ? 'flex items-center justify-center px-2 py-2.5 text-sm font-medium text-muted border-l-4 border-transparent rounded-r-xl hover:bg-cloud/60 hover:border-moss/40 hover:text-ink transition-colors'
      : 'flex items-center gap-3 px-4 py-2.5 text-sm font-medium text-muted border-l-4 border-transparent rounded-r-xl hover:bg-cloud/60 hover:border-moss/40 hover:text-ink transition-colors';
  }
}
