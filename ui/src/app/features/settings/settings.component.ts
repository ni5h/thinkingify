import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { UserProfileService } from '../../core/services/user-profile.service';
import { AuthService } from '../../core/services/auth.service';
import { AccountType } from '../../core/models/user';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [RouterLink],
  template: `
    <a routerLink="/dashboard" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
      &larr; Back
    </a>

    <h1 class="font-display text-3xl mt-4">Settings</h1>

    @if (me(); as profile) {
      <div class="flex flex-col gap-6 mt-8 max-w-md">
        <div>
          <p class="text-sm font-medium text-muted">Email</p>
          <p class="text-ink mt-1">{{ profile.email }}</p>
        </div>

        @if (profile.account_type) {
          <div>
            <p class="text-sm font-medium text-muted">Account type</p>
            <div class="flex gap-2 mt-2">
              <button
                type="button"
                (click)="setAccountType('parent')"
                [class.bg-moss]="profile.account_type === 'parent'"
                [class.text-white]="profile.account_type === 'parent'"
                [class.border-cloud]="profile.account_type !== 'parent'"
                class="rounded-xl border px-4 py-2 text-sm font-medium transition-colors"
              >
                Parent / guardian
              </button>
              <button
                type="button"
                (click)="setAccountType('child')"
                [class.bg-moss]="profile.account_type === 'child'"
                [class.text-white]="profile.account_type === 'child'"
                [class.border-cloud]="profile.account_type !== 'child'"
                class="rounded-xl border px-4 py-2 text-sm font-medium transition-colors"
              >
                Kid
              </button>
            </div>
            <p class="text-xs text-muted mt-2">Changes which fields show up on your Profile page. Your other details aren't affected.</p>
          </div>
        }

        <div>
          <button type="button" (click)="logout()" class="rounded-xl border border-cloud bg-paper px-5 py-2.5 text-sm font-medium text-ink hover:border-moss transition-colors">
            Log out
          </button>
        </div>

        <p class="text-sm text-muted border-t border-cloud pt-6">More settings — like notification preferences — will land here later.</p>
      </div>
    }
  `,
})
export default class SettingsComponent {
  private readonly userProfile = inject(UserProfileService);
  private readonly auth = inject(AuthService);

  readonly me = this.userProfile.me;

  async setAccountType(type: AccountType): Promise<void> {
    await this.userProfile.update({ account_type: type });
  }

  logout(): void {
    this.auth.logout();
  }
}
