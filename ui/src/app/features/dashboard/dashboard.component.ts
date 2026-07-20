import { Component, computed, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BlogService } from '../../core/services/blog.service';
import { ProgressService } from '../../core/services/progress.service';
import { ProfileService } from '../../core/services/profile.service';
import { PuzzleProgressService } from '../../core/services/puzzle-progress.service';

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

      @if (puzzlesAttempted() === 0) {
        <p class="text-muted mt-4">No puzzles attempted yet.</p>
      } @else {
        <div class="flex flex-wrap gap-4 mt-4">
          <div class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
            <p class="text-xs text-muted font-mono">Puzzles attempted</p>
            <p class="font-display text-3xl text-ink mt-1">{{ puzzlesAttempted() }}</p>
          </div>
          <div class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
            <p class="text-xs text-muted font-mono">This week</p>
            <p class="font-display text-3xl text-ink mt-1">{{ puzzlesAttemptedThisWeek() }}</p>
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
  private readonly profileService = inject(ProfileService);
  private readonly puzzleProgress = inject(PuzzleProgressService);

  readonly profile = this.profileService.profile;
  readonly streak = this.progress.currentStreak;

  private readonly publishedPosts = computed(() => this.blog.published() ?? []);
  readonly publishedCount = computed(() => this.publishedPosts().length);
  readonly recentPosts = computed(() => this.publishedPosts().slice(0, 3));

  private readonly puzzleStats = computed(() => this.puzzleProgress.stats() ?? []);
  readonly puzzlesAttempted = computed(() =>
    this.puzzleStats().reduce((sum, s) => sum + s.total_attempts, 0)
  );
  readonly puzzlesAttemptedThisWeek = computed(() =>
    this.puzzleStats().reduce((sum, s) => sum + s.attempts_this_week, 0)
  );
}
