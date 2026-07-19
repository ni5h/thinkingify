import { Component, computed, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BlogService } from '../../../core/services/blog.service';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-studio-dashboard',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    <div class="flex items-baseline justify-between gap-4">
      <div>
        <h1 class="font-display text-3xl">Welcome, {{ auth.currentUser()?.name }}</h1>
        <p class="text-muted mt-1">Thinkingify Studio</p>
      </div>
      <div class="flex gap-2">
        <a routerLink="/studio/topics" class="rounded-xl border border-cloud bg-paper px-5 py-2.5 text-sm font-medium text-ink hover:border-moss hover:bg-cloud/60 transition-colors">
          Rowling topics
        </a>
        <a routerLink="/studio/posts/new" class="rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors">
          New post
        </a>
      </div>
    </div>

    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8">
      <div class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
        <p class="text-xs text-muted font-mono">Drafts</p>
        <p class="font-display text-3xl text-ink mt-1">{{ draftCount() }}</p>
      </div>
      <div class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
        <p class="text-xs text-muted font-mono">Published</p>
        <p class="font-display text-3xl text-ink mt-1">{{ publishedCount() }}</p>
      </div>
      <div class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
        <p class="text-xs text-muted font-mono">Writing streak</p>
        <p class="font-display text-3xl text-ink mt-1">{{ writingStreak() }}</p>
      </div>
      <div class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
        <p class="text-xs text-muted font-mono">Total posts</p>
        <p class="font-display text-3xl text-ink mt-1">{{ (posts() ?? []).length }}</p>
      </div>
    </div>

    <div class="flex items-baseline justify-between gap-4 mt-10">
      <h2 class="font-display text-xl">Recent activity</h2>
      <a routerLink="/studio/posts" class="rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
        All posts &rarr;
      </a>
    </div>

    @if (recentActivity().length === 0) {
      <p class="text-muted mt-4">No activity yet. <a routerLink="/studio/posts/new" class="text-moss-dark hover:underline">Write your first post</a>.</p>
    } @else {
      <ul class="mt-4 flex flex-col gap-2">
        @for (post of recentActivity(); track post.id) {
          <li class="rounded-xl border border-cloud bg-white shadow-sm px-4 py-3 flex items-baseline justify-between gap-4">
            <span class="text-ink text-sm font-medium">{{ post.title || '(untitled)' }}</span>
            <span class="text-xs text-muted font-mono whitespace-nowrap">{{ post.status }} &middot; {{ post.updated_at | date: 'mediumDate' }}</span>
          </li>
        }
      </ul>
    }
  `,
})
export default class StudioDashboardComponent {
  private readonly blog = inject(BlogService);
  readonly auth = inject(AuthService);

  readonly posts = this.blog.all;

  readonly draftCount = computed(() => (this.posts() ?? []).filter((p) => p.status === 'draft').length);
  readonly publishedCount = computed(
    () => (this.posts() ?? []).filter((p) => p.status === 'published').length
  );

  readonly recentActivity = computed(() =>
    [...(this.posts() ?? [])].sort((a, b) => b.updated_at.localeCompare(a.updated_at)).slice(0, 5)
  );

  // Pragmatic Phase 1 approximation: distinct activity days derived from this
  // module's own updated_at/published_at timestamps, not the cross-module
  // activityDates ledger (which stays local to the other, untouched modules).
  readonly writingStreak = computed(() => {
    const dates = new Set(
      (this.posts() ?? [])
        .flatMap((p) => [p.updated_at?.slice(0, 10), p.published_at?.slice(0, 10)])
        .filter((d): d is string => !!d)
    );
    if (dates.size === 0) return 0;

    const sorted = [...dates].sort().reverse();
    const today = new Date().toISOString().slice(0, 10);
    const oneDayMs = 24 * 60 * 60 * 1000;

    let streak = 0;
    let cursor = new Date(today);
    for (const dateStr of sorted) {
      const cursorStr = cursor.toISOString().slice(0, 10);
      if (dateStr === cursorStr) {
        streak++;
        cursor = new Date(cursor.getTime() - oneDayMs);
      } else if (dateStr < cursorStr) {
        break;
      }
    }
    return streak;
  });
}
