import { Component, computed, effect, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BlogService } from '../../core/services/blog.service';
import { ProgressService } from '../../core/services/progress.service';
import { ProfileService } from '../../core/services/profile.service';
import { PuzzleProgressService } from '../../core/services/puzzle-progress.service';
import { FamilyService } from '../../core/services/family.service';
import { AuthService } from '../../core/services/auth.service';
import { ChildSummary, FamilyLink, TargetRole } from '../../core/models/family';
import { isKakoomaGameId } from '../sherlock/kakooma/kakooma.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    <h1 class="font-display text-2xl sm:text-3xl">Hello, {{ profile().name || 'there' }}.</h1>
    <p class="font-mono text-sm text-muted mt-1">{{ streak() }}-day thinking streak</p>

    <hr class="border-cloud mt-10" />

    <section class="mt-10">
      <h2 class="font-display text-xl">Blog</h2>

      @if (publishedCount() === 0) {
        <p class="text-muted mt-4">Nothing published yet.</p>
      } @else {
        <div class="rounded-2xl border border-cloud bg-white shadow-sm p-5 mt-4 inline-block">
          <p class="text-xs text-muted font-mono">Posts published</p>
          <p class="font-display text-3xl text-ink mt-1">{{ publishedCount() }}</p>
        </div>

        <h3 class="text-sm font-medium text-muted mt-6">Recent posts</h3>
        <ul class="mt-2 flex flex-col gap-2">
          @for (post of recentPosts(); track post.id) {
            <li>
              <a [routerLink]="['/blog', post.slug]" class="text-ink text-sm font-medium hover:underline">{{ post.title }}</a>
              <span class="text-xs text-muted font-mono ml-2">{{ post.published_at | date: 'mediumDate' }}</span>
            </li>
          }
        </ul>
      }

      <a routerLink="/blog" class="inline-block mt-4 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
        View all posts &rarr;
      </a>
    </section>

    <hr class="border-cloud mt-10" />

    <section class="mt-10">
      <h2 class="font-display text-xl">Sherlock Holmes</h2>

      @if (sherlockSummary().totalAttempts === 0) {
        <p class="text-muted mt-4">No puzzles attempted yet.</p>
      } @else {
        <div class="flex flex-wrap gap-4 mt-4">
          <div class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
            <p class="text-xs text-muted font-mono">Puzzles attempted</p>
            <p class="font-display text-3xl text-ink mt-1">{{ sherlockSummary().totalAttempts }}</p>
          </div>
          <div class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
            <p class="text-xs text-muted font-mono">This week</p>
            <p class="font-display text-3xl text-ink mt-1">{{ sherlockSummary().attemptsThisWeek }}</p>
          </div>
        </div>
      }

      <a routerLink="/sherlock" class="inline-block mt-4 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
        See Sherlock Holmes room &rarr;
      </a>
    </section>

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
              <button type="button" (click)="unlink(link.id)" class="mt-3 rounded-lg px-2.5 py-1 text-xs font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
                Unlink
              </button>
            </div>
          }
        </div>
      }

      @if (childLinks().length > 0) {
        <h3 class="text-sm font-medium text-muted mt-6">Your guardians</h3>
        <ul class="mt-2 flex flex-col gap-2">
          @for (link of childLinks(); track link.id) {
            <li class="text-sm text-ink flex items-center gap-3">
              {{ link.guardian.name }}
              <button type="button" (click)="unlink(link.id)" class="rounded-lg px-2 py-1 text-xs font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
                Unlink
              </button>
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
  `,
})
export default class DashboardComponent {
  private readonly blog = inject(BlogService);
  private readonly progress = inject(ProgressService);
  private readonly profileService = inject(ProfileService);
  private readonly puzzleProgress = inject(PuzzleProgressService);
  private readonly family = inject(FamilyService);
  private readonly auth = inject(AuthService);

  readonly profile = this.profileService.profile;
  readonly streak = this.progress.currentStreak;

  private readonly publishedPosts = computed(() => this.blog.published() ?? []);
  readonly publishedCount = computed(() => this.publishedPosts().length);
  readonly recentPosts = computed(() => this.publishedPosts().slice(0, 3));

  readonly sherlockSummary = this.puzzleProgress.roomStats(isKakoomaGameId);

  readonly incoming = computed(() => this.family.incoming() ?? []);
  readonly outgoing = computed(() => this.family.outgoing() ?? []);
  readonly guardianLinks = computed(() => this.family.links()?.as_guardian ?? []);
  readonly childLinks = computed(() => this.family.links()?.as_child ?? []);

  readonly linkEmail = signal('');
  readonly linkRole = signal<TargetRole>('child');
  readonly linking = signal(false);
  readonly linkError = signal<string | null>(null);

  readonly childSummaries = signal<Map<string, ChildSummary>>(new Map());

  constructor() {
    effect(() => {
      for (const link of this.guardianLinks()) {
        if (!this.childSummaries().has(link.child.id)) {
          void this.family.childSummary(link.child.id).then((summary) => {
            this.childSummaries.update((map) => new Map(map).set(link.child.id, summary));
          });
        }
      }
    });
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
