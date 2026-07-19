import { Component, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BlogService } from '../../../core/services/blog.service';
import { ContentStatus } from '../../../core/models/content';

const STATUS_LABELS: Record<ContentStatus, string> = {
  draft: 'Draft',
  pending_review: 'Pending review',
  published: 'Published',
  archived: 'Archived',
};

@Component({
  selector: 'app-studio-posts-list',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    <div class="flex items-baseline justify-between gap-4">
      <h1 class="font-display text-3xl">Posts</h1>
      <a routerLink="/studio/posts/new" class="rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors">
        New post
      </a>
    </div>

    @if ((posts() ?? []).length === 0) {
      <p class="text-muted mt-6">No posts yet. Start your first one.</p>
    } @else {
      <ul class="mt-8 flex flex-col gap-4">
        @for (post of posts(); track post.id) {
          <li class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
            <div class="flex items-start justify-between gap-4">
              <div>
                <h2 class="font-display text-xl text-ink">{{ post.title || '(untitled)' }}</h2>
                <p class="text-muted text-sm mt-1">{{ post.summary }}</p>
                <p class="text-xs text-muted font-mono mt-2">
                  {{ statusLabels[post.status] }} &middot; updated {{ post.updated_at | date: 'mediumDate' }}
                </p>
              </div>
            </div>

            <div class="flex flex-wrap gap-2 mt-4">
              <a [routerLink]="['/studio/posts', post.id, 'edit']" class="rounded-lg bg-cloud px-3 py-1.5 text-sm font-medium text-ink hover:bg-cloud/80 transition-colors">
                Edit
              </a>

              @if (post.status === 'draft') {
                <button type="button" (click)="submitForReview(post.id)" class="rounded-lg bg-moss/10 px-3 py-1.5 text-sm font-medium text-moss-dark hover:bg-moss/20 transition-colors">
                  Submit for review
                </button>
                <button type="button" (click)="remove(post.id)" class="rounded-lg px-3 py-1.5 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
                  Delete
                </button>
              }

              @if (post.status === 'pending_review') {
                <button type="button" (click)="publish(post.id)" class="rounded-lg bg-moss/10 px-3 py-1.5 text-sm font-medium text-moss-dark hover:bg-moss/20 transition-colors">
                  Publish
                </button>
                <button type="button" (click)="backToDraft(post.id)" class="rounded-lg px-3 py-1.5 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
                  Back to draft
                </button>
              }

              @if (post.status === 'published') {
                <a [routerLink]="['/blog', post.slug]" class="rounded-lg px-3 py-1.5 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
                  View live
                </a>
                <button type="button" (click)="archive(post.id)" class="rounded-lg bg-amber/10 px-3 py-1.5 text-sm font-medium text-amber hover:bg-amber/20 transition-colors">
                  Archive
                </button>
              }

              @if (post.status === 'archived') {
                <button type="button" (click)="republish(post.id)" class="rounded-lg bg-moss/10 px-3 py-1.5 text-sm font-medium text-moss-dark hover:bg-moss/20 transition-colors">
                  Republish
                </button>
                <button type="button" (click)="remove(post.id)" class="rounded-lg px-3 py-1.5 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
                  Delete
                </button>
              }
            </div>
          </li>
        }
      </ul>
    }
  `,
})
export default class StudioPostsListComponent {
  private readonly blog = inject(BlogService);

  readonly posts = this.blog.all;
  readonly statusLabels = STATUS_LABELS;

  submitForReview(id: string): void {
    void this.blog.submitForReview(id);
  }

  backToDraft(id: string): void {
    void this.blog.backToDraft(id);
  }

  publish(id: string): void {
    void this.blog.publish(id);
  }

  archive(id: string): void {
    void this.blog.archive(id);
  }

  republish(id: string): void {
    void this.blog.republish(id);
  }

  remove(id: string): void {
    if (confirm('Delete this post for good?')) {
      void this.blog.delete(id);
    }
  }
}
