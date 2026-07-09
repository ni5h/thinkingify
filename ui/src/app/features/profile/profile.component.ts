import { Component, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { ProfileService } from '../../core/services/profile.service';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [RouterLink],
  template: `
    <a routerLink="/" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
      &larr; Back
    </a>

    <h1 class="font-display text-3xl mt-4">Profile</h1>
    <p class="text-muted mt-1">Used to personalize the landing page. Nothing here leaves this device.</p>

    <div class="flex flex-col gap-5 mt-6 max-w-md">
      <label class="flex flex-col gap-1">
        <span class="text-sm font-medium text-muted">Name</span>
        <input
          type="text"
          maxlength="40"
          [value]="name()"
          (input)="name.set($any($event.target).value)"
          class="rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors"
        />
      </label>

      <label class="flex flex-col gap-1">
        <span class="text-sm font-medium text-muted">Short tagline</span>
        <input
          type="text"
          maxlength="80"
          placeholder="e.g. one curious eight-year-old"
          [value]="tagline()"
          (input)="tagline.set($any($event.target).value)"
          class="rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors"
        />
      </label>

      <div class="flex gap-3 mt-2">
        <button type="button" (click)="save()" class="rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors">
          Save
        </button>
        <a routerLink="/" class="rounded-xl px-5 py-2.5 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
          Cancel
        </a>
      </div>
    </div>
  `,
})
export default class ProfileComponent {
  private readonly profileService = inject(ProfileService);
  private readonly router = inject(Router);

  private readonly existing = this.profileService.profile();

  readonly name = signal(this.existing.name);
  readonly tagline = signal(this.existing.tagline);

  save(): void {
    this.profileService.update({ name: this.name().trim(), tagline: this.tagline().trim() });
    this.router.navigate(['/']);
  }
}
