import { Component, computed, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { marked } from 'marked';
import { BlogService } from '../../core/services/blog.service';

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
        @if (post()!.coverImageDataUrl) {
          <img [src]="post()!.coverImageDataUrl" [alt]="post()!.title" class="w-full h-64 object-cover rounded-2xl shadow-sm" />
        }
        <h1 class="font-display text-4xl text-ink mt-6">{{ post()!.title }}</h1>
        <p class="text-muted mt-2">{{ post()!.tagline }}</p>
        <p class="text-xs text-muted font-mono mt-3">{{ post()!.publishedAt | date: 'mediumDate' }}</p>
        <div class="markdown-content mt-8" [innerHTML]="renderedContent()"></div>
      </article>
    } @else {
      <p class="text-muted mt-6">Post not found.</p>
      <a routerLink="/blog" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-ink hover:bg-cloud/60 transition-colors">&larr; Back to Blog</a>
    }
  `,
})
export default class BlogPostComponent {
  private readonly blog = inject(BlogService);
  private readonly route = inject(ActivatedRoute);

  private readonly id = toSignal(this.route.paramMap, { requireSync: true });

  readonly post = computed(() => {
    const post = this.blog.getById(this.id().get('id') ?? '');
    return post?.status === 'published' ? post : undefined;
  });

  readonly renderedContent = computed(() => {
    const post = this.post();
    return post ? marked.parse(post.contentMarkdown, { async: false }) : '';
  });
}
