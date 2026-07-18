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

// Structural scaffolding only, shown as TipTap ghost text — never written
// into getMarkdown(), vanishes on first keystroke. Never generated content,
// consistent with the app's "no AI writes for him" rule.
const STYLE_PLACEHOLDERS: Record<WritingStyle, string> = {
  documentary: "What's your opening fact?",
  story: 'Who are your friends talking about this?',
  fun_casual: "Okay, so here's the deal...",
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

          <div #editorEl class="markdown-content rounded-xl border border-cloud px-4 py-3 min-h-[16rem] mt-4 focus-within:border-moss transition-colors"></div>

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

    const placeholder = post.style ? STYLE_PLACEHOLDERS[post.style] : 'Start writing...';
    this.editor = new Editor({
      element: this.editorEl()!.nativeElement,
      extensions: [StarterKit, Markdown, Placeholder.configure({ placeholder })],
      content: post.content_markdown,
      contentType: 'markdown',
      onUpdate: () => this.scheduleAutosave(),
    });
  }

  ngOnDestroy(): void {
    if (this.autosaveTimer) clearTimeout(this.autosaveTimer);
    this.editor?.destroy();
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
