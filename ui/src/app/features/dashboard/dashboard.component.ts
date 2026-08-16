import { Component, computed, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BlogService } from '../../core/services/blog.service';
import { ProgressService } from '../../core/services/progress.service';
import { UserProfileService } from '../../core/services/user-profile.service';
import { PuzzleProgressService } from '../../core/services/puzzle-progress.service';
import { FamilyService } from '../../core/services/family.service';
import { AuthService } from '../../core/services/auth.service';
import { FamilyLink } from '../../core/models/family';
import { isKakoomaGameId } from '../sherlock/kakooma/kakooma.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    <h1 class="font-display text-2xl sm:text-3xl">Hello, {{ greetingName() }}.</h1>
    <p class="font-mono text-sm text-muted mt-1">{{ streak() }}-day thinking streak</p>

    @if (incoming().length > 0) {
      <section class="mt-8">
        <h2 class="font-display text-xl">Family</h2>
        <ul class="mt-3 flex flex-col gap-2">
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
      </section>
    } @else if (showConnectNudge()) {
      <section class="mt-8">
        <a routerLink="/profile" class="block rounded-2xl border border-cloud bg-white shadow-sm p-5 hover:border-moss transition-colors">
          <p class="font-display text-lg text-ink">Connect your family</p>
          <p class="text-sm text-muted mt-1">Link a parent or child so grown-ups can follow along and approve posts.</p>
        </a>
      </section>
    }

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
  `,
})
export default class DashboardComponent {
  private readonly blog = inject(BlogService);
  private readonly progress = inject(ProgressService);
  private readonly userProfile = inject(UserProfileService);
  private readonly puzzleProgress = inject(PuzzleProgressService);
  private readonly family = inject(FamilyService);
  private readonly auth = inject(AuthService);

  readonly greetingName = computed(() => this.userProfile.me()?.first_name || 'there');
  readonly streak = this.progress.currentStreak;

  readonly incoming = computed(() => this.family.incoming() ?? []);
  // Only nudge once we know the user has no links either way — while the
  // resource is still loading (undefined) we stay quiet to avoid a flash.
  readonly showConnectNudge = computed(() => {
    const links = this.family.links();
    if (!links) return false;
    return links.as_guardian.length === 0 && links.as_child.length === 0;
  });

  private otherParty(req: FamilyLink) {
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

  private readonly publishedPosts = computed(() => this.blog.published() ?? []);
  readonly publishedCount = computed(() => this.publishedPosts().length);
  readonly recentPosts = computed(() => this.publishedPosts().slice(0, 3));

  readonly sherlockSummary = this.puzzleProgress.roomStats(isKakoomaGameId);
}
