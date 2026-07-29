import {
  Component,
  HostListener,
  OnDestroy,
  OnInit,
  computed,
  effect,
  inject,
  signal,
  viewChild,
  viewChildren,
} from '@angular/core';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { Editor } from '@tiptap/core';
import { StarterKit } from '@tiptap/starter-kit';
import { Markdown } from '@tiptap/markdown';
import { Placeholder } from '@tiptap/extension-placeholder';
import { BlogService } from '../../../core/services/blog.service';
import { NoteService } from '../../../core/services/note.service';
import { NotesPanelComponent } from '../../../shared/components/notes-panel/notes-panel.component';
import { EditorToolbarComponent } from '../../../shared/components/editor-toolbar/editor-toolbar.component';
import { applyToolbarCommand, computeActiveMarks, ToolbarCommand } from '../../../shared/components/editor-toolbar/apply-toolbar-command';
import { SectionEditorComponent } from './section-editor/section-editor.component';
import { CompanionPanelComponent } from './companion-panel/companion-panel.component';
import { StyleScaffold } from './style-scaffolds';
import { assembleSectionMarkdown, resolveEditorMode } from './section-markdown';

const AUTOSAVE_DELAY_MS = 3000;
const FREEFORM_PLACEHOLDER = 'Start writing...';

type EditorViewMode = 'loading' | 'scaffolded' | 'blank';

@Component({
  selector: 'app-writing-studio',
  standalone: true,
  imports: [RouterLink, NotesPanelComponent, EditorToolbarComponent, SectionEditorComponent, CompanionPanelComponent],
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
    } @else if (mode() === 'loading') {
      <p class="text-muted mt-6">Loading&hellip;</p>
    } @else {
      <div class="flex items-baseline justify-between gap-4 mt-4">
        <h1 class="font-display text-3xl">{{ title() || 'Your writing' }}</h1>
        @if (autosaveStatus()) {
          <span class="text-xs text-muted font-mono">{{ autosaveStatus() }}</span>
        }
      </div>

      <div class="md:flex md:gap-6 mt-6">
        <div [class]="maximized()
          ? 'fixed inset-0 z-50 bg-paper overflow-y-auto p-6 md:p-10'
          : 'md:flex-1 min-w-0'"
        >
          <label class="flex flex-col gap-1">
            <span class="text-sm font-medium text-muted">Title</span>
            <input
              type="text"
              [value]="title()"
              (input)="onTitleInput($any($event.target).value)"
              class="rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors"
            />
          </label>

          <div class="flex justify-end gap-2 mt-2">
            @if (topicId() && !maximized()) {
              <button
                type="button"
                (click)="chatOpen.set(!chatOpen())"
                class="rounded-lg px-2.5 py-1.5 text-sm text-muted hover:bg-cloud hover:text-ink transition-colors"
              >
                {{ chatOpen() ? 'Hide writing buddy' : 'Writing buddy' }}
              </button>
            }
            <button
              type="button"
              (click)="toggleMaximized()"
              class="rounded-lg px-2.5 py-1.5 text-sm text-muted hover:bg-cloud hover:text-ink transition-colors"
            >
              {{ maximized() ? 'Exit fullscreen' : 'Fullscreen' }}
            </button>
          </div>

          @if (mode() === 'scaffolded') {
            <div class="flex flex-col gap-5 mt-2">
              @for (section of revealedSections(); track section.id) {
                <app-section-editor
                  [section]="section"
                  [initialMarkdown]="sectionContent()[section.id]"
                  (markdownChange)="onSectionChange(section.id, $event)"
                />
              }
              @if (revealedCount() < totalSections()) {
                <button
                  type="button"
                  (click)="revealNext()"
                  class="self-start rounded-xl border border-cloud bg-paper px-5 py-2.5 text-sm font-medium text-ink hover:border-moss hover:bg-cloud/60 transition-colors"
                >
                  Next part &rarr;
                </button>
              }
            </div>
          } @else {
            <div class="mt-2">
              <app-editor-toolbar [activeMarks]="activeMarks()" (command)="onCommand($event)" />
              <div #editorEl class="markdown-content rounded-b-xl border border-cloud px-4 py-3 min-h-[16rem] focus-within:border-moss transition-colors"></div>
            </div>
          }

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

        @if (!maximized()) {
          <aside class="md:w-80 shrink-0 mt-8 md:mt-0">
            <app-notes-panel [body]="noteBody()" [status]="null" (bodyChange)="noteBody.set($event)" (blurred)="saveNote()" />
          </aside>
        }
      </div>

      @if (topicId() && chatOpen() && !maximized()) {
        <div class="fixed inset-0 z-40 bg-ink/20" (click)="chatOpen.set(false)"></div>
        <div class="fixed inset-y-0 right-0 z-50 w-full sm:w-96 bg-paper border-l border-cloud shadow-lg p-4 flex flex-col">
          <button
            type="button"
            (click)="chatOpen.set(false)"
            class="self-end rounded-lg px-3 py-1.5 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors mb-2"
          >
            Close
          </button>
          <div class="flex-1 min-h-0">
            <app-companion-panel [contentId]="postId" [sessionId]="companionSessionId" />
          </div>
        </div>
      }
    }
  `,
})
export default class WritingStudioComponent implements OnInit, OnDestroy {
  private readonly blog = inject(BlogService);
  private readonly noteService = inject(NoteService);
  private readonly route = inject(ActivatedRoute);

  private readonly editorEl = viewChild<{ nativeElement: HTMLElement }>('editorEl');
  private readonly sectionEditors = viewChildren(SectionEditorComponent);

  readonly postId = this.route.snapshot.paramMap.get('id')!;

  readonly title = signal('');
  readonly noteBody = signal('');
  readonly autosaveStatus = signal<string | null>(null);
  readonly publishing = signal(false);
  readonly published = signal(false);
  readonly publishedSlug = signal('');
  readonly copied = signal(false);
  readonly error = signal<string | null>(null);
  readonly maximized = signal(false);
  // Opens a fixed-position drawer over the page (not a flex column) since
  // the app shell caps every route's content at max-w-3xl — a docked
  // third column has no room to grow into at any viewport width.
  readonly chatOpen = signal(false);
  // Session boundary for the writing companion — one continuous Writing
  // Studio visit is one session, regardless of how many times the chat
  // panel itself is opened/closed within that visit.
  readonly companionSessionId = crypto.randomUUID();

  readonly mode = signal<EditorViewMode>('loading');
  readonly scaffold = signal<StyleScaffold | null>(null);
  readonly sectionContent = signal<Record<string, string>>({});
  readonly revealedCount = signal(1);
  private readonly blankSeed = signal('');

  readonly revealedSections = computed(() => this.scaffold()?.sections?.slice(0, this.revealedCount()) ?? []);
  readonly totalSections = computed(() => this.scaffold()?.sections?.length ?? 0);

  readonly activeMarks = signal<Set<string>>(new Set());

  readonly topicId = signal<string | null>(null);
  private editor?: Editor;
  private autosaveTimer?: ReturnType<typeof setTimeout>;

  constructor() {
    // Blank mode's single editor mounts here instead of ngAfterViewInit —
    // its #editorEl div only exists once `mode()` resolves to 'blank'
    // (after the async post fetch), so mounting has to react to both the
    // element appearing and the mode becoming known.
    effect(() => {
      const el = this.editorEl();
      if (el && this.mode() === 'blank' && !this.editor) {
        this.mountBlankEditor(el.nativeElement);
      }
    });
  }

  async ngOnInit(): Promise<void> {
    const post = await this.blog.getById(this.postId);
    if (!post) return;

    this.title.set(post.title);
    if (post.status === 'published') {
      this.published.set(true);
      this.publishedSlug.set(post.slug);
    }
    if (post.topic_id) {
      this.topicId.set(post.topic_id);
      const note = await this.noteService.getOrCreate(post.topic_id);
      this.noteBody.set(note.body);
    }

    const resolved = resolveEditorMode(post.style, post.content_markdown);
    if (resolved.mode === 'blank') {
      this.blankSeed.set(resolved.seed);
      this.mode.set('blank');
    } else {
      this.scaffold.set(resolved.scaffold);
      this.sectionContent.set(resolved.content);
      this.revealedCount.set(resolved.revealedCount);
      this.mode.set('scaffolded');
    }
  }

  ngOnDestroy(): void {
    if (this.autosaveTimer) clearTimeout(this.autosaveTimer);
    this.editor?.destroy();
  }

  private mountBlankEditor(element: HTMLElement): void {
    this.editor = new Editor({
      element,
      extensions: [StarterKit, Markdown, Placeholder.configure({ placeholder: FREEFORM_PLACEHOLDER })],
      content: this.blankSeed(),
      contentType: 'markdown',
      onUpdate: () => {
        this.syncActiveMarks();
        this.scheduleAutosave();
      },
      onSelectionUpdate: () => this.syncActiveMarks(),
    });
    this.syncActiveMarks();
  }

  private syncActiveMarks(): void {
    // Same TipTap quirk as section-editor.component.ts: seeding non-trivial
    // initial content can trigger onUpdate synchronously during `new
    // Editor(...)`, before `this.editor` is assigned.
    if (!this.editor) return;
    this.activeMarks.set(computeActiveMarks(this.editor));
  }

  onCommand(command: ToolbarCommand): void {
    if (this.editor) applyToolbarCommand(this.editor, command);
  }

  onSectionChange(sectionId: string, markdown: string): void {
    this.sectionContent.update((map) => ({ ...map, [sectionId]: markdown }));
    this.scheduleAutosave();
  }

  revealNext(): void {
    const total = this.totalSections();
    const nextCount = Math.min(this.revealedCount() + 1, total);
    if (nextCount === this.revealedCount()) return;
    this.revealedCount.set(nextCount);
    // Newly-revealed section's SectionEditorComponent mounts its own
    // editor asynchronously in its own ngAfterViewInit — defer the focus
    // call to the next tick so it's actually there to receive it.
    setTimeout(() => this.sectionEditors()[nextCount - 1]?.focusEditor(), 0);
  }

  toggleMaximized(): void {
    this.maximized.update((v) => !v);
  }

  @HostListener('document:keydown.escape')
  onEscapeKey(): void {
    if (this.maximized()) this.maximized.set(false);
  }

  onTitleInput(value: string): void {
    this.title.set(value);
    this.scheduleAutosave();
  }

  private scheduleAutosave(): void {
    if (this.autosaveTimer) clearTimeout(this.autosaveTimer);
    this.autosaveTimer = setTimeout(() => void this.autosave(), AUTOSAVE_DELAY_MS);
  }

  private currentMarkdown(): string {
    if (this.mode() === 'scaffolded') {
      const scaffold = this.scaffold();
      return scaffold?.sections
        ? assembleSectionMarkdown(scaffold.sections, this.sectionContent(), this.revealedCount())
        : '';
    }
    return this.editor?.getMarkdown() ?? this.blankSeed();
  }

  private async autosave(): Promise<void> {
    try {
      await this.blog.update(this.postId, {
        title: this.title(),
        content_markdown: this.currentMarkdown(),
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
        content_markdown: this.currentMarkdown(),
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
    const topicId = this.topicId();
    if (!topicId) return;
    await this.noteService.update(topicId, this.noteBody());
  }

  async copyLink(): Promise<void> {
    const url = `${window.location.origin}/blog/${this.publishedSlug()}`;
    await navigator.clipboard.writeText(url);
    this.copied.set(true);
  }
}
