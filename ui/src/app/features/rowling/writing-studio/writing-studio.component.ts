import { AfterViewInit, Component, OnDestroy, inject, signal, viewChild } from '@angular/core';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { Editor } from '@tiptap/core';
import { StarterKit } from '@tiptap/starter-kit';
import { Markdown } from '@tiptap/markdown';
import { Placeholder } from '@tiptap/extension-placeholder';
import { BlogService } from '../../../core/services/blog.service';
import { NoteService } from '../../../core/services/note.service';
import { WritingStyle } from '../../../core/models/content';
import { NotesPanelComponent } from '../../../shared/components/notes-panel/notes-panel.component';

const AUTOSAVE_DELAY_MS = 3000;
const FREEFORM_PLACEHOLDER = 'Start writing...';

// Structural scaffolding only — headings the kid fills in under, never
// generated prose, consistent with the app's "no AI writes for him" rule.
// Seeded once into a brand-new draft's editor content (see
// ngAfterViewInit); 'freeform' intentionally has no entry — a clean slate
// with just the placeholder ghost text below.
const STYLE_TEMPLATES: Partial<Record<WritingStyle, string>> = {
  documentary: '## What is it?\n\n\n## Why does it happen?\n\n\n## One fact that surprised me\n\n',
  story: '## The situation\n\n\n## What happened\n\n\n## How it turned out\n\n',
  fun_casual: '## The wildest part\n\n\n## My take\n\n',
};

@Component({
  selector: 'app-writing-studio',
  standalone: true,
  imports: [RouterLink, NotesPanelComponent],
  template: `
    <a routerLink="/rowling" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
      &larr; Back to Rowling
    </a>

    @if (published()) {
      <div class="max-w-md mx-auto mt-16 rounded-2xl border border-cloud bg-white shadow-sm p-8 text-center">
        <h1 class="font-display text-2xl text-ink">Published!</h1>
        <p class="text-muted mt-2">Your writing is live &mdash; share it with your friends.</p>
        <a [routerLink]="['/blog', publishedSlug()]" class="inline-block mt-4 text-moss font-medium hover:underline">
          View your post
        </a>
        <button
          type="button"
          (click)="copyLink()"
          class="block w-full mt-3 rounded-xl border border-cloud bg-paper px-5 py-2.5 text-sm font-medium text-ink hover:border-moss hover:bg-cloud/60 transition-colors"
        >
          {{ copied() ? 'Link copied!' : 'Copy link' }}
        </button>
      </div>
    } @else {
      <div class="flex items-baseline justify-between gap-4 mt-4">
        <h1 class="font-display text-3xl">{{ title() || 'Your writing' }}</h1>
        @if (autosaveStatus()) {
          <span class="text-xs text-muted font-mono">{{ autosaveStatus() }}</span>
        }
      </div>

      <div class="md:flex md:gap-6 mt-6">
        <div class="md:flex-1 min-w-0">
          <label class="flex flex-col gap-1">
            <span class="text-sm font-medium text-muted">Title</span>
            <input
              type="text"
              [value]="title()"
              (input)="onTitleInput($any($event.target).value)"
              class="rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors"
            />
          </label>

          <div class="flex flex-wrap gap-1 rounded-t-xl border border-cloud border-b-0 px-3 py-2 bg-paper mt-4">
            <button type="button" (click)="toggleBold()" [class]="markClass('bold')">B</button>
            <button type="button" (click)="toggleItalic()" [class]="markClass('italic')">I</button>
            <button type="button" (click)="toggleHeading(2)" [class]="markClass('heading2')">H2</button>
            <button type="button" (click)="toggleHeading(3)" [class]="markClass('heading3')">H3</button>
            <button type="button" (click)="toggleBulletList()" [class]="markClass('bulletList')">&bull; List</button>
            <button type="button" (click)="toggleOrderedList()" [class]="markClass('orderedList')">1. List</button>
            <button type="button" (click)="toggleBlockquote()" [class]="markClass('blockquote')">Quote</button>
          </div>
          <div #editorEl class="markdown-content rounded-b-xl border border-cloud px-4 py-3 min-h-[16rem] focus-within:border-moss transition-colors"></div>

          <button
            type="button"
            (click)="publish()"
            [disabled]="publishing()"
            class="mt-4 rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors disabled:opacity-60"
          >
            {{ publishing() ? 'Publishing…' : 'Publish to your blog' }}
          </button>

          @if (error()) {
            <p class="text-amber text-sm mt-2">{{ error() }}</p>
          }
        </div>

        <aside class="md:w-80 shrink-0 mt-8 md:mt-0">
          <app-notes-panel [body]="noteBody()" [status]="null" (bodyChange)="noteBody.set($event)" (blurred)="saveNote()" />
        </aside>
      </div>
    }
  `,
})
export default class WritingStudioComponent implements AfterViewInit, OnDestroy {
  private readonly blog = inject(BlogService);
  private readonly noteService = inject(NoteService);
  private readonly route = inject(ActivatedRoute);

  private readonly editorEl = viewChild<{ nativeElement: HTMLElement }>('editorEl');

  readonly postId = this.route.snapshot.paramMap.get('id')!;

  readonly title = signal('');
  readonly noteBody = signal('');
  readonly autosaveStatus = signal<string | null>(null);
  readonly publishing = signal(false);
  readonly published = signal(false);
  readonly publishedSlug = signal('');
  readonly copied = signal(false);
  readonly error = signal<string | null>(null);

  private readonly activeMarks = signal<Set<string>>(new Set());

  private topicId: string | null = null;
  private editor!: Editor;
  private autosaveTimer?: ReturnType<typeof setTimeout>;

  async ngAfterViewInit(): Promise<void> {
    const post = await this.blog.getById(this.postId);
    if (!post) return;

    this.title.set(post.title);
    if (post.status === 'published') {
      this.published.set(true);
      this.publishedSlug.set(post.slug);
    }
    if (post.topic_id) {
      this.topicId = post.topic_id;
      const note = await this.noteService.getOrCreate(post.topic_id);
      this.noteBody.set(note.body);
    }

    // A template is only ever seeded into a brand-new, still-empty draft —
    // re-opening a draft the kid has already started writing in never
    // overwrites their work with the template again.
    const hasExistingContent = !!post.content_markdown?.trim();
    const initialContent = hasExistingContent
      ? post.content_markdown
      : post.style
        ? (STYLE_TEMPLATES[post.style] ?? '')
        : '';

    this.editor = new Editor({
      element: this.editorEl()!.nativeElement,
      extensions: [StarterKit, Markdown, Placeholder.configure({ placeholder: FREEFORM_PLACEHOLDER })],
      content: initialContent,
      contentType: 'markdown',
      onUpdate: () => {
        this.syncActiveMarks();
        this.scheduleAutosave();
      },
      onSelectionUpdate: () => this.syncActiveMarks(),
    });
    this.syncActiveMarks();
  }

  ngOnDestroy(): void {
    if (this.autosaveTimer) clearTimeout(this.autosaveTimer);
    this.editor?.destroy();
  }

  private syncActiveMarks(): void {
    // Seeding non-trivial initial content (a style template) can trigger a
    // plugin-driven transaction dispatch synchronously during `new Editor(...)`
    // itself — before the constructor call has returned and been assigned to
    // `this.editor` — so `onUpdate` can fire once with `this.editor` still
    // undefined. An empty editor (freeform / editing existing content) never
    // hits this, only the template-seeding path does.
    if (!this.editor) return;
    const active = new Set<string>();
    if (this.editor.isActive('bold')) active.add('bold');
    if (this.editor.isActive('italic')) active.add('italic');
    if (this.editor.isActive('heading', { level: 2 })) active.add('heading2');
    if (this.editor.isActive('heading', { level: 3 })) active.add('heading3');
    if (this.editor.isActive('bulletList')) active.add('bulletList');
    if (this.editor.isActive('orderedList')) active.add('orderedList');
    if (this.editor.isActive('blockquote')) active.add('blockquote');
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

  onTitleInput(value: string): void {
    this.title.set(value);
    this.scheduleAutosave();
  }

  private scheduleAutosave(): void {
    if (this.autosaveTimer) clearTimeout(this.autosaveTimer);
    this.autosaveTimer = setTimeout(() => void this.autosave(), AUTOSAVE_DELAY_MS);
  }

  private async autosave(): Promise<void> {
    try {
      await this.blog.update(this.postId, {
        title: this.title(),
        content_markdown: this.editor.getMarkdown(),
      });
      this.autosaveStatus.set(`Autosaved ${new Date().toLocaleTimeString()}`);
    } catch {
      this.autosaveStatus.set('Autosave failed');
    }
  }

  async publish(): Promise<void> {
    this.publishing.set(true);
    this.error.set(null);
    try {
      await this.blog.update(this.postId, {
        title: this.title(),
        content_markdown: this.editor.getMarkdown(),
      });
      await this.blog.selfPublish(this.postId);
      const post = await this.blog.getById(this.postId);
      this.publishedSlug.set(post?.slug ?? '');
      this.published.set(true);
    } catch {
      this.error.set('Could not publish. Please try again.');
    } finally {
      this.publishing.set(false);
    }
  }

  async saveNote(): Promise<void> {
    if (!this.topicId) return;
    await this.noteService.update(this.topicId, this.noteBody());
  }

  async copyLink(): Promise<void> {
    const url = `${window.location.origin}/blog/${this.publishedSlug()}`;
    await navigator.clipboard.writeText(url);
    this.copied.set(true);
  }
}
