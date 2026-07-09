import { AfterViewInit, Component, OnDestroy, computed, inject, signal, viewChild } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Editor } from '@tiptap/core';
import { StarterKit } from '@tiptap/starter-kit';
import { Markdown } from '@tiptap/markdown';
import { Placeholder } from '@tiptap/extension-placeholder';
import { BlogService } from '../../../core/services/blog.service';
import { resizeAndCompressImage } from '../../../core/utils/image';

const AUTOSAVE_DELAY_MS = 3000;
const WORDS_PER_MINUTE = 200;

@Component({
  selector: 'app-studio-post-editor',
  standalone: true,
  imports: [RouterLink],
  template: `
    <a routerLink="/studio/posts" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
      &larr; Back to posts
    </a>

    <div class="flex items-baseline justify-between gap-4 mt-4">
      <h1 class="font-display text-3xl">{{ postId ? 'Edit Post' : 'New Post' }}</h1>
      @if (autosaveStatus()) {
        <span class="text-xs text-muted font-mono">{{ autosaveStatus() }}</span>
      }
    </div>

    <div class="flex flex-col gap-5 mt-6">
      <label class="flex flex-col gap-1">
        <span class="text-sm font-medium text-muted">Title</span>
        <input
          type="text"
          [value]="title()"
          (input)="title.set($any($event.target).value)"
          class="rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors"
        />
      </label>

      <label class="flex flex-col gap-1">
        <span class="text-sm font-medium text-muted">Summary</span>
        <input
          type="text"
          [value]="summary()"
          (input)="summary.set($any($event.target).value)"
          class="rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors"
        />
      </label>

      <label class="flex flex-col gap-1">
        <span class="text-sm font-medium text-muted">Feature image (optional)</span>
        <input type="file" accept="image/*" [disabled]="uploadingImage()" (change)="onFeatureImageSelected($event)" />
        @if (uploadingImage()) {
          <p class="text-xs text-muted mt-1">Uploading…</p>
        }
        @if (featureImageUrl()) {
          <div class="mt-2 flex items-start gap-3">
            <img [src]="featureImageUrl()" alt="Feature preview" class="h-32 w-auto object-cover rounded-xl border border-cloud" />
            <button type="button" (click)="featureImageUrl.set(undefined)" class="rounded-lg px-3 py-1.5 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
              Remove
            </button>
          </div>
        }
      </label>

      <div class="flex flex-col gap-1">
        <div class="flex items-baseline justify-between">
          <span class="text-sm font-medium text-muted">Content</span>
          <span class="text-xs text-muted font-mono">{{ wordCount() }} words &middot; {{ readingMinutes() }} min read</span>
        </div>

        <div class="flex flex-wrap gap-1 rounded-t-xl border border-cloud border-b-0 px-3 py-2 bg-paper">
          <button type="button" (click)="toggleBold()" [class]="markClass('bold')">B</button>
          <button type="button" (click)="toggleItalic()" [class]="markClass('italic')">I</button>
          <button type="button" (click)="toggleStrike()" [class]="markClass('strike')">S</button>
          <button type="button" (click)="toggleHeading(2)" [class]="markClass('heading2')">H2</button>
          <button type="button" (click)="toggleHeading(3)" [class]="markClass('heading3')">H3</button>
          <button type="button" (click)="toggleBulletList()" [class]="markClass('bulletList')">&bull; List</button>
          <button type="button" (click)="toggleOrderedList()" [class]="markClass('orderedList')">1. List</button>
          <button type="button" (click)="toggleBlockquote()" [class]="markClass('blockquote')">Quote</button>
          <button type="button" (click)="toggleCodeBlock()" [class]="markClass('codeBlock')">Code</button>
          <button type="button" (click)="setLink()" [class]="markClass('link')">Link</button>
        </div>

        <div #editorEl class="markdown-content rounded-b-xl border border-cloud px-4 py-3 min-h-[16rem] focus-within:border-moss transition-colors"></div>
      </div>

      <div class="flex gap-3 mt-2">
        <button type="button" (click)="save()" [disabled]="saving()" class="rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors disabled:opacity-60">
          {{ saving() ? 'Saving…' : 'Save' }}
        </button>
        <a routerLink="/studio/posts" class="rounded-xl px-5 py-2.5 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
          Cancel
        </a>
      </div>

      @if (error()) {
        <p class="text-amber text-sm">{{ error() }}</p>
      }
    </div>
  `,
})
export default class StudioPostEditorComponent implements AfterViewInit, OnDestroy {
  private readonly blog = inject(BlogService);
  private readonly http = inject(HttpClient);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  private readonly editorEl = viewChild<{ nativeElement: HTMLElement }>('editorEl');

  readonly postId = this.route.snapshot.paramMap.get('id') ?? undefined;

  readonly title = signal('');
  readonly summary = signal('');
  readonly featureImageUrl = signal<string | undefined>(undefined);
  readonly uploadingImage = signal(false);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly autosaveStatus = signal<string | null>(null);

  private readonly activeMarks = signal<Set<string>>(new Set());
  readonly wordCount = signal(0);
  readonly readingMinutes = computed(() => Math.max(1, Math.ceil(this.wordCount() / WORDS_PER_MINUTE)));

  private editor!: Editor;
  private autosaveTimer?: ReturnType<typeof setTimeout>;

  async ngAfterViewInit(): Promise<void> {
    let initialMarkdown = '';

    if (this.postId) {
      const existing = await this.blog.getById(this.postId);
      if (existing) {
        this.title.set(existing.title);
        this.summary.set(existing.summary ?? '');
        this.featureImageUrl.set(existing.feature_image_url ?? undefined);
        initialMarkdown = existing.content_markdown;
      }
    }

    this.editor = new Editor({
      element: this.editorEl()!.nativeElement,
      extensions: [
        StarterKit.configure({ link: { openOnClick: false } }),
        Markdown,
        Placeholder.configure({ placeholder: 'Start writing...' }),
      ],
      content: initialMarkdown,
      contentType: 'markdown',
      onUpdate: () => {
        this.syncActiveMarks();
        this.syncWordCount();
        this.scheduleAutosave();
      },
      onSelectionUpdate: () => this.syncActiveMarks(),
    });
    this.syncActiveMarks();
    this.syncWordCount();
  }

  ngOnDestroy(): void {
    if (this.autosaveTimer) clearTimeout(this.autosaveTimer);
    this.editor?.destroy();
  }

  private syncWordCount(): void {
    const text = this.editor.getText().trim();
    this.wordCount.set(text ? text.split(/\s+/).length : 0);
  }

  private scheduleAutosave(): void {
    // Only autosave an existing post — a brand-new post needs an explicit
    // first Save to get an id to PATCH against.
    if (!this.postId) return;
    if (this.autosaveTimer) clearTimeout(this.autosaveTimer);
    this.autosaveTimer = setTimeout(() => void this.autosave(), AUTOSAVE_DELAY_MS);
  }

  private async autosave(): Promise<void> {
    if (!this.postId) return;
    try {
      await this.blog.update(this.postId, {
        title: this.title(),
        summary: this.summary(),
        content_markdown: this.editor.getMarkdown(),
        feature_image_url: this.featureImageUrl(),
      });
      this.autosaveStatus.set(`Autosaved ${new Date().toLocaleTimeString()}`);
    } catch {
      this.autosaveStatus.set('Autosave failed');
    }
  }

  private syncActiveMarks(): void {
    const active = new Set<string>();
    if (this.editor.isActive('bold')) active.add('bold');
    if (this.editor.isActive('italic')) active.add('italic');
    if (this.editor.isActive('strike')) active.add('strike');
    if (this.editor.isActive('heading', { level: 2 })) active.add('heading2');
    if (this.editor.isActive('heading', { level: 3 })) active.add('heading3');
    if (this.editor.isActive('bulletList')) active.add('bulletList');
    if (this.editor.isActive('orderedList')) active.add('orderedList');
    if (this.editor.isActive('blockquote')) active.add('blockquote');
    if (this.editor.isActive('codeBlock')) active.add('codeBlock');
    if (this.editor.isActive('link')) active.add('link');
    this.activeMarks.set(active);
  }

  markClass(name: string): string {
    const active = this.activeMarks().has(name);
    return active
      ? 'rounded-lg bg-moss/10 px-2.5 py-1.5 text-sm font-medium text-moss-dark'
      : 'rounded-lg px-2.5 py-1.5 text-sm text-muted hover:bg-cloud hover:text-ink transition-colors';
  }

  toggleBold(): void {
    this.editor.chain().focus().toggleBold().run();
  }

  toggleItalic(): void {
    this.editor.chain().focus().toggleItalic().run();
  }

  toggleStrike(): void {
    this.editor.chain().focus().toggleStrike().run();
  }

  toggleHeading(level: 2 | 3): void {
    this.editor.chain().focus().toggleHeading({ level }).run();
  }

  toggleBulletList(): void {
    this.editor.chain().focus().toggleBulletList().run();
  }

  toggleOrderedList(): void {
    this.editor.chain().focus().toggleOrderedList().run();
  }

  toggleBlockquote(): void {
    this.editor.chain().focus().toggleBlockquote().run();
  }

  toggleCodeBlock(): void {
    this.editor.chain().focus().toggleCodeBlock().run();
  }

  setLink(): void {
    const previousUrl = this.editor.getAttributes('link')['href'] as string | undefined;
    const url = window.prompt('Link URL', previousUrl ?? 'https://');
    if (url === null) return;
    if (url === '') {
      this.editor.chain().focus().extendMarkRange('link').unsetLink().run();
      return;
    }
    this.editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
  }

  async onFeatureImageSelected(event: Event): Promise<void> {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;

    this.uploadingImage.set(true);
    this.error.set(null);
    try {
      const blob = await resizeAndCompressImage(file);
      const formData = new FormData();
      formData.append('file', blob, 'feature-image.jpg');
      const response = await firstValueFrom(
        this.http.post<{ url: string }>('/api/v1/uploads/feature-image', formData)
      );
      this.featureImageUrl.set(response.url);
    } catch {
      this.error.set('Image upload failed. Please try again.');
    } finally {
      this.uploadingImage.set(false);
    }
  }

  async save(): Promise<void> {
    this.saving.set(true);
    this.error.set(null);
    try {
      const draft = {
        title: this.title(),
        summary: this.summary(),
        content_markdown: this.editor.getMarkdown(),
        feature_image_url: this.featureImageUrl(),
      };

      if (this.postId) {
        await this.blog.update(this.postId, draft);
      } else {
        await this.blog.create(draft);
      }

      await this.router.navigate(['/studio/posts']);
    } catch {
      this.error.set('Could not save this post. Please try again.');
      this.saving.set(false);
    }
  }
}
