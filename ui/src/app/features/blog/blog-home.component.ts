import { Component, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BlogService } from '../../core/services/blog.service';

@Component({
  selector: 'app-blog-home',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    <div class="flex items-baseline justify-between gap-4">
      <h1 class="font-display text-3xl">Blog</h1>
      <a routerLink="/studio" class="rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
        Thinkingify Studio
      </a>
    </div>

    @if ((posts() ?? []).length === 0) {
      <p class="text-muted mt-6">Nothing published yet.</p>
    } @else {
      <div class="mt-8 flex flex-col gap-8">
        @for (post of posts(); track post.id) {
          <a [routerLink]="['/blog', post.slug]" class="block rounded-2xl border border-cloud bg-white shadow-sm overflow-hidden hover:shadow-md transition-shadow">
            @if (post.feature_image_url) {
              <img [src]="post.feature_image_url" [alt]="post.title" class="w-full h-48 object-cover" />
            }
            <div class="p-6">
              <h2 class="font-display text-2xl text-ink">{{ post.title }}</h2>
              <p class="text-muted mt-1">{{ post.summary }}</p>
              <p class="text-xs text-muted font-mono mt-3">{{ post.published_at | date: 'mediumDate' }}</p>
            </div>
          </a>
        }
      </div>
    }
  `,
})
export default class BlogHomeComponent {
  private readonly blog = inject(BlogService);

  readonly posts = this.blog.published;
}
