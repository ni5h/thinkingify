import { Component, computed, effect, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { UserProfileService } from '../../core/services/user-profile.service';
import { FamilyService } from '../../core/services/family.service';
import { AuthService } from '../../core/services/auth.service';
import { BlogService } from '../../core/services/blog.service';
import { AccountType, UserLinkedProfile } from '../../core/models/user';
import { ChildSummary, FamilyLink, TargetRole } from '../../core/models/family';
import { ContentListItem } from '../../core/models/content';
import { ParentReport } from '../../core/models/parent-report';
import { resizeAndCompressImage } from '../../core/utils/image';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [RouterLink],
  template: `
    <a routerLink="/dashboard" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
      &larr; Back
    </a>

    <h1 class="font-display text-3xl mt-4">Profile</h1>

    @if (!me()) {
      <p class="text-muted mt-6">Loading your profile&hellip;</p>
    } @else if (!me()!.account_type) {
      <p class="text-muted mt-1">Let's set up your profile. Are you a parent or a kid?</p>
      <div class="flex gap-3 mt-6">
        <button type="button" (click)="chooseAccountType('parent')" class="rounded-xl border border-cloud bg-white shadow-sm px-6 py-5 text-left hover:border-moss transition-colors">
          <p class="font-display text-lg text-ink">I'm a parent</p>
          <p class="text-sm text-muted mt-1">or another grown-up guardian</p>
        </button>
        <button type="button" (click)="chooseAccountType('child')" class="rounded-xl border border-cloud bg-white shadow-sm px-6 py-5 text-left hover:border-moss transition-colors">
          <p class="font-display text-lg text-ink">I'm a kid</p>
          <p class="text-sm text-muted mt-1">writing, learning, exploring</p>
        </button>
      </div>
    } @else {
      <div class="max-w-md mt-6">
        <div class="rounded-xl bg-cloud/60 h-2 overflow-hidden">
          <div class="bg-moss h-full transition-all" [style.width.%]="me()!.profile_completion_percent"></div>
        </div>
        <p class="text-xs text-muted font-mono mt-1.5">Profile {{ me()!.profile_completion_percent }}% complete</p>
      </div>

      <div class="flex items-center gap-4 mt-6">
        @if (me()!.avatar_url) {
          <img [src]="me()!.avatar_url" alt="Your avatar" class="h-16 w-16 rounded-full object-cover border border-cloud" />
        } @else {
          <div class="h-16 w-16 rounded-full bg-cloud flex items-center justify-center font-display text-xl text-muted">
            {{ (firstName() || me()!.name || '?').charAt(0) }}
          </div>
        }
        <label class="rounded-xl border border-cloud bg-paper px-4 py-2 text-sm font-medium text-ink hover:border-moss transition-colors cursor-pointer">
          {{ uploadingAvatar() ? 'Uploading…' : 'Change photo' }}
          <input type="file" accept="image/*" class="hidden" [disabled]="uploadingAvatar()" (change)="onAvatarSelected($event)" />
        </label>
      </div>

      <div class="flex flex-col gap-5 mt-8 max-w-md">
        <div class="grid grid-cols-2 gap-4">
          <label class="flex flex-col gap-1">
            <span class="text-sm font-medium text-muted">First name</span>
            <input type="text" maxlength="100" [value]="firstName()" (input)="firstName.set($any($event.target).value)" class="rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-sm font-medium text-muted">Last name</span>
            <input type="text" maxlength="100" [value]="lastName()" (input)="lastName.set($any($event.target).value)" class="rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors" />
          </label>
        </div>

        <label class="flex flex-col gap-1">
          <span class="text-sm font-medium text-muted">Username</span>
          <input type="text" maxlength="30" placeholder="shown on posts you publish" [value]="username()" (input)="username.set($any($event.target).value)" class="rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors" />
          <span class="text-xs text-muted">If left blank, your first name is shown instead. Your last name is never shown publicly.</span>
        </label>

        <label class="flex flex-col gap-1">
          <span class="text-sm font-medium text-muted">Short tagline</span>
          <input type="text" maxlength="140" placeholder="e.g. one curious eight-year-old" [value]="tagline()" (input)="tagline.set($any($event.target).value)" class="rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors" />
        </label>

        @if (me()!.account_type === 'child') {
          <label class="flex flex-col gap-1">
            <span class="text-sm font-medium text-muted">School</span>
            <input type="text" maxlength="150" [value]="schoolName()" (input)="schoolName.set($any($event.target).value)" class="rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors" />
          </label>
        } @else {
          <label class="flex flex-col gap-1">
            <span class="text-sm font-medium text-muted">What do you do? <span class="text-muted font-normal">(optional)</span></span>
            <input type="text" maxlength="150" [value]="occupation()" (input)="occupation.set($any($event.target).value)" class="rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors" />
          </label>
        }

        <div class="grid grid-cols-3 gap-3">
          <label class="flex flex-col gap-1">
            <span class="text-sm font-medium text-muted">City</span>
            <input type="text" maxlength="100" [value]="city()" (input)="city.set($any($event.target).value)" class="rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-sm font-medium text-muted">State</span>
            <input type="text" maxlength="100" [value]="stateField()" (input)="stateField.set($any($event.target).value)" class="rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-sm font-medium text-muted">Country</span>
            <input type="text" maxlength="100" [value]="country()" (input)="country.set($any($event.target).value)" class="rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors" />
          </label>
        </div>
        <p class="text-xs text-muted -mt-3">Helps us personalize. Totally optional, and never shown publicly.</p>

        @if (formError()) {
          <p class="text-amber text-sm">{{ formError() }}</p>
        }

        <div class="flex gap-3 mt-2">
          <button type="button" (click)="saveDetails()" [disabled]="saving()" class="rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors disabled:opacity-60">
            {{ saving() ? 'Saving…' : 'Save' }}
          </button>
        </div>
      </div>

      <hr class="border-cloud mt-10" />

      <section class="mt-10">
        <h2 class="font-display text-xl">Family</h2>

        @if (incoming().length > 0) {
          <h3 class="text-sm font-medium text-muted mt-6">Requests for you</h3>
          <ul class="mt-2 flex flex-col gap-2">
            @for (req of incoming(); track req.id) {
              <li class="rounded-2xl border border-cloud bg-white shadow-sm p-4 flex items-center justify-between gap-3">
                <span class="text-sm text-ink">{{ requestDescription(req) }}</span>
                <span class="flex gap-2 shrink-0">
                  <button type="button" (click)="accept(req.id)" class="rounded-lg bg-moss/10 px-3 py-1.5 text-sm font-medium text-moss-dark hover:bg-moss/20 transition-colors">
                    Accept
                  </button>
                  <button type="button" (click)="decline(req.id)" class="rounded-lg px-3 py-1.5 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
                    Decline
                  </button>
                </span>
              </li>
            }
          </ul>
        }

        @if (outgoing().length > 0) {
          <h3 class="text-sm font-medium text-muted mt-6">Waiting for a reply</h3>
          <ul class="mt-2 flex flex-col gap-2">
            @for (req of outgoing(); track req.id) {
              <li class="text-sm text-muted">
                {{ otherParty(req).name }} &mdash; waiting for them to accept
              </li>
            }
          </ul>
        }

        @if (guardianLinks().length > 0) {
          <h3 class="text-sm font-medium text-muted mt-6">Linked</h3>
          <div class="flex flex-wrap gap-4 mt-2">
            @for (link of guardianLinks(); track link.id) {
              <div class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
                <p class="font-display text-lg text-ink">{{ link.child.name }}</p>
                @if (childSummaries().get(link.child.id); as s) {
                  <p class="text-xs text-muted font-mono mt-1">
                    {{ s.total_puzzle_attempts }} puzzles &middot; {{ s.puzzle_attempts_this_week }} this week &middot; {{ s.published_post_count }} posts
                  </p>
                }
                <div class="flex gap-2 mt-3">
                  <button type="button" (click)="toggleProfile(link.child.id)" class="rounded-lg px-2.5 py-1 text-xs font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
                    {{ expandedUserId() === link.child.id ? 'Hide profile' : 'View profile' }}
                  </button>
                  <button type="button" (click)="toggleReview(link.child.id)" class="rounded-lg px-2.5 py-1 text-xs font-medium text-moss-dark bg-moss/10 hover:bg-moss/20 transition-colors">
                    {{ reviewButtonLabel(link.child.id) }}
                  </button>
                  <button type="button" (click)="unlink(link.id)" class="rounded-lg px-2.5 py-1 text-xs font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
                    Unlink
                  </button>
                </div>
                @if (expandedUserId() === link.child.id && expandedProfile(); as p) {
                  <div class="mt-3 pt-3 border-t border-cloud text-sm text-muted">
                    @if (p.school_name) { <p>School: {{ p.school_name }}</p> }
                    @if (p.location_city || p.location_country) { <p>{{ formatLocation(p) }}</p> }
                    @if (p.tagline) { <p class="italic mt-1">"{{ p.tagline }}"</p> }
                  </div>
                }
                @if (expandedReviewId() === link.child.id) {
                  <div class="mt-3 pt-3 border-t border-cloud flex flex-col gap-3">
                    @if (pendingReviewItems(link.child.id).length === 0 && publishedItems(link.child.id).length === 0) {
                      <p class="text-sm text-muted">Nothing to review right now.</p>
                    }
                    @for (item of pendingReviewItems(link.child.id); track item.id) {
                      <div class="rounded-xl border border-cloud p-3">
                        <p class="text-sm font-medium text-ink">{{ item.title || '(untitled)' }}</p>
                        @if (item.summary) {
                          <p class="text-xs text-muted mt-1">{{ item.summary }}</p>
                        }
                        <div class="flex gap-2 mt-2">
                          <button type="button" (click)="approve(link.child.id, item.id)" class="rounded-lg bg-moss/10 px-2.5 py-1 text-xs font-medium text-moss-dark hover:bg-moss/20 transition-colors">
                            Approve
                          </button>
                          <button type="button" (click)="reject(link.child.id, item.id)" class="rounded-lg px-2.5 py-1 text-xs font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
                            Reject
                          </button>
                          @if (reportForContent(link.child.id, item.id); as report) {
                            <a [routerLink]="['/profile/reports', link.child.id, report.id]" class="rounded-lg px-2.5 py-1 text-xs font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
                              View report
                            </a>
                          }
                        </div>
                      </div>
                    }
                    @if (publishedItems(link.child.id).length > 0) {
                      <p class="text-xs font-medium text-muted">Published</p>
                      @for (item of publishedItems(link.child.id); track item.id) {
                        <div class="rounded-xl border border-cloud p-3 flex items-center justify-between gap-3">
                          <p class="text-sm text-ink">{{ item.title || '(untitled)' }}</p>
                          <span class="flex items-center gap-2 shrink-0">
                            @if (reportForContent(link.child.id, item.id); as report) {
                              <a [routerLink]="['/profile/reports', link.child.id, report.id]" class="rounded-lg px-2.5 py-1 text-xs font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
                                View report
                              </a>
                            }
                            <button type="button" (click)="unpublish(link.child.id, item.id)" class="rounded-lg bg-amber/10 px-2.5 py-1 text-xs font-medium text-amber hover:bg-amber/20 transition-colors">
                              Unpublish
                            </button>
                          </span>
                        </div>
                      }
                    }
                  </div>
                }
              </div>
            }
          </div>
        }

        @if (childLinks().length > 0) {
          <h3 class="text-sm font-medium text-muted mt-6">Your guardians</h3>
          <ul class="mt-2 flex flex-col gap-2">
            @for (link of childLinks(); track link.id) {
              <li class="rounded-2xl border border-cloud bg-white shadow-sm p-4">
                <div class="flex items-center gap-3">
                  <span class="text-sm text-ink">{{ link.guardian.name }}</span>
                  <button type="button" (click)="toggleProfile(link.guardian.id)" class="rounded-lg px-2 py-1 text-xs font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
                    {{ expandedUserId() === link.guardian.id ? 'Hide profile' : 'View profile' }}
                  </button>
                  <button type="button" (click)="unlink(link.id)" class="rounded-lg px-2 py-1 text-xs font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
                    Unlink
                  </button>
                </div>
                @if (expandedUserId() === link.guardian.id && expandedProfile(); as p) {
                  <div class="mt-3 pt-3 border-t border-cloud text-sm text-muted">
                    @if (p.occupation) { <p>{{ p.occupation }}</p> }
                    @if (p.location_city || p.location_country) { <p>{{ formatLocation(p) }}</p> }
                    @if (p.tagline) { <p class="italic mt-1">"{{ p.tagline }}"</p> }
                  </div>
                }
              </li>
            }
          </ul>
        }

        <h3 class="text-sm font-medium text-muted mt-6">Link a family member</h3>
        <div class="flex flex-wrap items-center gap-2 mt-2">
          <input
            type="email"
            placeholder="their email"
            [value]="linkEmail()"
            (input)="linkEmail.set($any($event.target).value)"
            class="rounded-xl border border-cloud bg-paper px-3 py-2.5 text-sm focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors"
          />
          <select
            [value]="linkRole()"
            (change)="linkRole.set($any($event.target).value)"
            class="rounded-xl border border-cloud bg-paper px-3 py-2.5 text-sm focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors"
          >
            <option value="child">Invite as my child</option>
            <option value="guardian">Invite as my guardian</option>
          </select>
          <button
            type="button"
            (click)="sendLinkRequest()"
            [disabled]="linking() || !linkEmail()"
            class="rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors disabled:opacity-60"
          >
            {{ linking() ? 'Sending…' : 'Send request' }}
          </button>
        </div>
        @if (linkError()) {
          <p class="text-amber text-sm mt-2">{{ linkError() }}</p>
        }
      </section>
    }
  `,
})
export default class ProfileComponent {
  private readonly userProfile = inject(UserProfileService);
  private readonly family = inject(FamilyService);
  private readonly auth = inject(AuthService);
  private readonly blog = inject(BlogService);

  readonly me = this.userProfile.me;

  readonly firstName = signal('');
  readonly lastName = signal('');
  readonly username = signal('');
  readonly tagline = signal('');
  readonly schoolName = signal('');
  readonly occupation = signal('');
  readonly city = signal('');
  readonly stateField = signal('');
  readonly country = signal('');

  readonly saving = signal(false);
  readonly formError = signal<string | null>(null);
  readonly uploadingAvatar = signal(false);

  private readonly formInitialized = signal(false);

  readonly incoming = computed(() => this.family.incoming() ?? []);
  readonly outgoing = computed(() => this.family.outgoing() ?? []);
  readonly guardianLinks = computed(() => this.family.links()?.as_guardian ?? []);
  readonly childLinks = computed(() => this.family.links()?.as_child ?? []);

  readonly linkEmail = signal('');
  readonly linkRole = signal<TargetRole>('child');
  readonly linking = signal(false);
  readonly linkError = signal<string | null>(null);

  readonly childSummaries = signal<Map<string, ChildSummary>>(new Map());

  readonly expandedUserId = signal<string | null>(null);
  readonly expandedProfile = signal<UserLinkedProfile | null>(null);

  readonly reviewContent = signal<Map<string, ContentListItem[]>>(new Map());
  readonly expandedReviewId = signal<string | null>(null);
  readonly childReportsMap = signal<Map<string, ParentReport[]>>(new Map());

  constructor() {
    effect(() => {
      const profile = this.me();
      if (profile && !this.formInitialized()) {
        this.firstName.set(profile.first_name ?? '');
        this.lastName.set(profile.last_name ?? '');
        this.username.set(profile.username ?? '');
        this.tagline.set(profile.tagline ?? '');
        this.schoolName.set(profile.school_name ?? '');
        this.occupation.set(profile.occupation ?? '');
        this.city.set(profile.location_city ?? '');
        this.stateField.set(profile.location_state ?? '');
        this.country.set(profile.location_country ?? '');
        this.formInitialized.set(true);
      }
    });

    effect(() => {
      for (const link of this.guardianLinks()) {
        if (!this.childSummaries().has(link.child.id)) {
          void this.family.childSummary(link.child.id).then((summary) => {
            this.childSummaries.update((map) => new Map(map).set(link.child.id, summary));
          });
        }
        if (!this.reviewContent().has(link.child.id)) {
          void this.family.childContent(link.child.id).then((content) => {
            this.reviewContent.update((map) => new Map(map).set(link.child.id, content));
          });
        }
        if (!this.childReportsMap().has(link.child.id)) {
          void this.family.childReports(link.child.id).then((reports) => {
            this.childReportsMap.update((map) => new Map(map).set(link.child.id, reports));
          });
        }
      }
    });
  }

  async chooseAccountType(type: AccountType): Promise<void> {
    await this.userProfile.update({ account_type: type });
  }

  async onAvatarSelected(event: Event): Promise<void> {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    this.uploadingAvatar.set(true);
    this.formError.set(null);
    try {
      const blob = await resizeAndCompressImage(file, 400, 0.8);
      const url = await this.userProfile.uploadAvatar(blob);
      await this.userProfile.update({ avatar_url: url });
    } catch {
      this.formError.set('Photo upload failed. Please try again.');
    } finally {
      this.uploadingAvatar.set(false);
    }
  }

  async saveDetails(): Promise<void> {
    this.saving.set(true);
    this.formError.set(null);
    try {
      await this.userProfile.update({
        first_name: this.firstName().trim() || undefined,
        last_name: this.lastName().trim() || undefined,
        username: this.username().trim() || undefined,
        tagline: this.tagline().trim() || undefined,
        school_name: this.schoolName().trim() || undefined,
        occupation: this.occupation().trim() || undefined,
        location_city: this.city().trim() || undefined,
        location_state: this.stateField().trim() || undefined,
        location_country: this.country().trim() || undefined,
      });
    } catch (err) {
      const detail = (err as { error?: { detail?: string } })?.error?.detail;
      this.formError.set(detail ?? 'Could not save your profile. Please try again.');
    } finally {
      this.saving.set(false);
    }
  }

  formatLocation(p: UserLinkedProfile): string {
    return [p.location_city, p.location_state, p.location_country].filter((v) => v).join(', ');
  }

  async toggleProfile(userId: string): Promise<void> {
    if (this.expandedUserId() === userId) {
      this.expandedUserId.set(null);
      this.expandedProfile.set(null);
      return;
    }
    this.expandedUserId.set(userId);
    this.expandedProfile.set(await this.userProfile.linkedProfile(userId));
  }

  pendingReviewItems(childId: string): ContentListItem[] {
    return (this.reviewContent().get(childId) ?? []).filter((item) => item.status === 'pending_review');
  }

  publishedItems(childId: string): ContentListItem[] {
    return (this.reviewContent().get(childId) ?? []).filter((item) => item.status === 'published');
  }

  reviewButtonLabel(childId: string): string {
    if (this.expandedReviewId() === childId) return 'Hide';
    const count = this.pendingReviewItems(childId).length;
    return count > 0 ? `Review ${count} post${count === 1 ? '' : 's'}` : 'Manage posts';
  }

  toggleReview(childId: string): void {
    this.expandedReviewId.set(this.expandedReviewId() === childId ? null : childId);
  }

  // Most recent report for this content item, if one exists — reports
  // list is already ordered newest-first, so the first match is the
  // latest (a rejected-and-resubmitted piece can have more than one).
  // Older content submitted before this feature shipped has none.
  reportForContent(childId: string, contentId: string): ParentReport | undefined {
    return (this.childReportsMap().get(childId) ?? []).find((r) => r.content_id === contentId);
  }

  private async refreshChildContent(childId: string): Promise<void> {
    const [content, summary, reports] = await Promise.all([
      this.family.childContent(childId),
      this.family.childSummary(childId),
      this.family.childReports(childId),
    ]);
    this.reviewContent.update((map) => new Map(map).set(childId, content));
    this.childSummaries.update((map) => new Map(map).set(childId, summary));
    this.childReportsMap.update((map) => new Map(map).set(childId, reports));
  }

  async approve(childId: string, contentId: string): Promise<void> {
    await this.blog.publish(contentId);
    await this.refreshChildContent(childId);
  }

  async reject(childId: string, contentId: string): Promise<void> {
    await this.blog.backToDraft(contentId);
    await this.refreshChildContent(childId);
  }

  async unpublish(childId: string, contentId: string): Promise<void> {
    await this.blog.archive(contentId);
    await this.refreshChildContent(childId);
  }

  // The party in a request that isn't the current user.
  otherParty(req: FamilyLink) {
    return this.auth.currentUser()?.id === req.guardian.id ? req.child : req.guardian;
  }

  requestDescription(req: FamilyLink): string {
    const iAmGuardian = this.auth.currentUser()?.id === req.guardian.id;
    const other = this.otherParty(req);
    return iAmGuardian ? `${other.name} wants you to be their guardian` : `${other.name} wants to be your guardian`;
  }

  async accept(linkId: string): Promise<void> {
    await this.family.accept(linkId);
  }

  async decline(linkId: string): Promise<void> {
    await this.family.decline(linkId);
  }

  async unlink(linkId: string): Promise<void> {
    await this.family.unlink(linkId);
  }

  async sendLinkRequest(): Promise<void> {
    this.linking.set(true);
    this.linkError.set(null);
    try {
      await this.family.sendRequest(this.linkEmail(), this.linkRole());
      this.linkEmail.set('');
    } catch (err) {
      const detail = (err as { error?: { detail?: string } })?.error?.detail;
      this.linkError.set(detail ?? 'Could not send that request. Please try again.');
    } finally {
      this.linking.set(false);
    }
  }
}
