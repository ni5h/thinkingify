import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { marked } from 'marked';
import { BlogService } from '../../core/services/blog.service';
import { Content } from '../../core/models/content';

@Component({
  selector: 'app-blog-post',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    @if (post()) {
      <a routerLink="/blog" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
        &larr; Back to Blog
      </a>

      <article class="mt-6">
        @if (post()!.feature_image_url) {
          <img [src]="post()!.feature_image_url" [alt]="post()!.title" class="w-full h-64 object-cover rounded-2xl shadow-sm" />
        }
        <h1 class="font-display text-4xl text-ink mt-6">{{ post()!.title }}</h1>
        <p class="text-muted mt-2">{{ post()!.summary }}</p>
        <p class="text-xs text-muted font-mono mt-3">{{ post()!.published_at | date: 'mediumDate' }}</p>
        <div class="markdown-content mt-8" [innerHTML]="renderedContent()"></div>
      </article>
    } @else if (post() === null) {
      <p class="text-muted mt-6">Post not found.</p>
      <a routerLink="/blog" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-ink hover:bg-cloud/60 transition-colors">&larr; Back to Blog</a>
    }
  `,
})
export default class BlogPostComponent implements OnInit {
  private readonly blog = inject(BlogService);
  private readonly route = inject(ActivatedRoute);

  private readonly slug = this.route.snapshot.paramMap.get('slug') ?? '';

  // undefined while loading, null when the slug doesn't resolve to a
  // published post (server enforces this — see /content/published/{slug}).
  readonly post = signal<Content | null | undefined>(undefined);

  readonly renderedContent = computed(() => {
    const post = this.post();
    return post ? marked.parse(post.content_markdown, { async: false }) : '';
  });

  async ngOnInit(): Promise<void> {
    const post = await this.blog.getPublishedBySlug(this.slug);
    this.post.set(post ?? null);
  }
}
