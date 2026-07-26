import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { IconComponent, IconName } from '../../shared/components/icon/icon.component';
import { AuthService } from '../../core/services/auth.service';
import { UserProfileService } from '../../core/services/user-profile.service';

interface NavItem {
  label: string;
  path: string;
  icon: IconName;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', path: '/dashboard', icon: 'home' },
  { label: 'Rowling', path: '/rowling', icon: 'rowling' },
  { label: 'Ramanujan', path: '/ramanujan', icon: 'puzzle' },
  { label: 'Einstein', path: '/einstein', icon: 'learn' },
  { label: 'Sherlock Holmes', path: '/sherlock', icon: 'sherlock' },
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

      <!-- User menu: deliberately separate from the 6-item NAV_ITEMS array
           above (which also drives the mobile bottom tab bar, kept fixed
           at 6 tabs) -->
      <div class="mt-auto px-3 py-4 border-t border-cloud">
        @if (auth.isAuthenticated()) {
          <a routerLink="/profile" [attr.title]="collapsed() ? 'Profile' : null" class="flex items-center gap-3 rounded-xl px-2 py-2 hover:bg-cloud/60 transition-colors">
            @if (me()?.avatar_url) {
              <img [src]="me()!.avatar_url" alt="" class="h-8 w-8 rounded-full object-cover shrink-0" />
            } @else {
              <div class="h-8 w-8 rounded-full bg-cloud flex items-center justify-center text-xs font-display text-muted shrink-0">
                {{ avatarInitial() }}
              </div>
            }
            @if (!collapsed()) {
              <span class="text-sm font-medium text-ink truncate">{{ displayName() }}</span>
            }
          </a>
          <a routerLink="/settings" [attr.title]="collapsed() ? 'Settings' : null" class="flex items-center gap-3 px-2 py-2 mt-1 rounded-xl text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
            <app-icon name="settings" [size]="18" />
            @if (!collapsed()) {
              <span>Settings</span>
            }
          </a>
        } @else {
          <a routerLink="/studio/login" [attr.title]="collapsed() ? 'Log in' : null" class="flex items-center gap-3 px-2 py-2 rounded-xl text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
            <app-icon name="log-in" [size]="18" />
            @if (!collapsed()) {
              <span>Log in</span>
            }
          </a>
        }
      </div>
    </nav>

    <!-- Mobile top bar: the desktop sidebar's wordmark-to-/ link has no
         equivalent in the bottom tab bar below (which is deliberately just
         the 6 module tabs, not a 7th "mission page" tab), so give mobile a
         separate way back to / here. Right side is the same user-menu entry
         point as the desktop sidebar footer. -->
    <div class="md:hidden fixed top-0 left-0 right-0 z-10 bg-paper border-b border-cloud px-4 py-3 flex items-center justify-between">
      <a routerLink="/" class="font-display text-lg text-ink hover:text-moss transition-colors">Thinkingify</a>
      @if (auth.isAuthenticated()) {
        <a routerLink="/profile">
          @if (me()?.avatar_url) {
            <img [src]="me()!.avatar_url" alt="" class="h-8 w-8 rounded-full object-cover" />
          } @else {
            <div class="h-8 w-8 rounded-full bg-cloud flex items-center justify-center text-xs font-display text-muted">{{ avatarInitial() }}</div>
          }
        </a>
      } @else {
        <a routerLink="/studio/login" class="rounded-lg px-3 py-1.5 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">Log in</a>
      }
    </div>

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
  readonly auth = inject(AuthService);
  private readonly userProfile = inject(UserProfileService);
  readonly me = this.userProfile.me;

  readonly items = NAV_ITEMS;
  readonly collapsed = signal(false);

  readonly displayName = computed(() => this.me()?.first_name || this.me()?.name || 'You');
  readonly avatarInitial = computed(() => this.displayName().charAt(0).toUpperCase());

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
