import { Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { marked } from 'marked';
import { BlogService } from '../../core/services/blog.service';
import { resizeAndCompressImage } from '../../core/utils/image';

@Component({
  selector: 'app-blog-editor',
  standalone: true,
  imports: [RouterLink],
  template: `
    <a routerLink="/blog/manage" class="text-sm text-muted hover:text-ink border-b border-transparent hover:border-ink">
      &larr; Back to manage
    </a>

    <h1 class="font-display text-3xl mt-4">{{ postId ? 'Edit Post' : 'New Post' }}</h1>

    <div class="flex flex-col gap-5 mt-6">
      <label class="flex flex-col gap-1">
        <span class="text-sm font-medium text-muted">Title</span>
        <input
          type="text"
          [value]="title()"
          (input)="title.set($any($event.target).value)"
          class="border border-cloud px-3 py-2 bg-paper"
        />
      </label>

      <label class="flex flex-col gap-1">
        <span class="text-sm font-medium text-muted">Tagline</span>
        <input
          type="text"
          [value]="tagline()"
          (input)="tagline.set($any($event.target).value)"
          class="border border-cloud px-3 py-2 bg-paper"
        />
      </label>

      <label class="flex flex-col gap-1">
        <span class="text-sm font-medium text-muted">Cover image (optional)</span>
        <input type="file" accept="image/*" (change)="onCoverImageSelected($event)" />
        @if (coverImageDataUrl()) {
          <div class="mt-2 flex items-start gap-3">
            <img [src]="coverImageDataUrl()" alt="Cover preview" class="h-32 w-auto object-cover border border-cloud" />
            <button type="button" (click)="coverImageDataUrl.set(undefined)" class="text-sm text-muted border-b border-muted">
              Remove
            </button>
          </div>
        }
      </label>

      <div class="flex flex-col gap-1">
        <div class="flex items-baseline justify-between">
          <span class="text-sm font-medium text-muted">Content (Markdown)</span>
          <button type="button" (click)="previewing.set(!previewing())" class="text-sm text-ink border-b border-ink">
            {{ previewing() ? 'Edit' : 'Preview' }}
          </button>
        </div>

        @if (previewing()) {
          <div class="markdown-content border border-cloud px-4 py-3 min-h-[16rem]" [innerHTML]="renderedPreview()"></div>
        } @else {
          <textarea
            rows="16"
            [value]="contentMarkdown()"
            (input)="contentMarkdown.set($any($event.target).value)"
            class="border border-cloud px-3 py-2 bg-paper font-mono text-sm"
          ></textarea>
        }
      </div>

      <div class="flex gap-3 mt-2">
        <button type="button" (click)="save()" class="bg-moss text-white border-l-4 border-moss-dark px-4 py-2 text-sm font-medium">
          Save
        </button>
        <a routerLink="/blog/manage" class="text-muted border-l-4 border-transparent px-4 py-2 text-sm font-medium">
          Cancel
        </a>
      </div>
    </div>
  `,
})
export default class BlogEditorComponent {
  private readonly blog = inject(BlogService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly postId = this.route.snapshot.paramMap.get('id') ?? undefined;

  private readonly existingPost = this.postId ? this.blog.getById(this.postId) : undefined;

  readonly title = signal(this.existingPost?.title ?? '');
  readonly tagline = signal(this.existingPost?.tagline ?? '');
  readonly contentMarkdown = signal(this.existingPost?.contentMarkdown ?? '');
  readonly coverImageDataUrl = signal<string | undefined>(this.existingPost?.coverImageDataUrl);
  readonly previewing = signal(false);

  readonly renderedPreview = computed(() => marked.parse(this.contentMarkdown(), { async: false }));

  async onCoverImageSelected(event: Event): Promise<void> {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    this.coverImageDataUrl.set(await resizeAndCompressImage(file));
  }

  save(): void {
    const draft = {
      title: this.title(),
      tagline: this.tagline(),
      contentMarkdown: this.contentMarkdown(),
      coverImageDataUrl: this.coverImageDataUrl(),
    };

    if (this.postId) {
      this.blog.update(this.postId, draft);
    } else {
      this.blog.create(draft);
    }

    this.router.navigate(['/blog/manage']);
  }
}
