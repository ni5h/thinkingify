import { Component, OnDestroy, OnInit, computed, effect, inject, signal, viewChild } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { marked } from 'marked';
import { Editor } from '@tiptap/core';
import { StarterKit } from '@tiptap/starter-kit';
import { Markdown } from '@tiptap/markdown';
import { Placeholder } from '@tiptap/extension-placeholder';
import { BlogService } from '../../../core/services/blog.service';
import { DiaryService } from '../../../core/services/diary.service';
import { NoteService } from '../../../core/services/note.service';
import { FamilyService } from '../../../core/services/family.service';
import { NotesPanelComponent } from '../../../shared/components/notes-panel/notes-panel.component';
import { EditorToolbarComponent } from '../../../shared/components/editor-toolbar/editor-toolbar.component';
import { CompanionPanelComponent } from '../writing-studio/companion-panel/companion-panel.component';
import { applyToolbarCommand, computeActiveMarks, ToolbarCommand } from '../../../shared/components/editor-toolbar/apply-toolbar-command';
import { resizeAndCompressImage } from '../../../core/utils/image';
import { DIARY_THEME_LIST, DiaryThemeKey, resolveDiaryTheme } from './diary-themes';

const AUTOSAVE_DELAY_MS = 3000;
const DIARY_PLACEHOLDER = 'Dear diary, today...';

@Component({
  selector: 'app-diary-editor',
  standalone: true,
  imports: [RouterLink, NotesPanelComponent, EditorToolbarComponent, CompanionPanelComponent],
  template: `
    <div class="flex items-center justify-between gap-3">
      <a routerLink="/rowling/diary" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
        &larr; My Diary
      </a>
      <div class="flex items-center gap-2">
        @if (autosaveStatus()) {
          <span class="text-xs text-muted font-mono">{{ autosaveStatus() }}</span>
        }
        <button type="button" (click)="notesOpen.set(!notesOpen())" class="rounded-lg px-2.5 py-1.5 text-sm text-muted hover:bg-cloud hover:text-ink transition-colors">
          {{ notesOpen() ? 'Hide notes' : 'Notes' }}
        </button>
        <button type="button" (click)="chatOpen.set(!chatOpen())" class="rounded-lg px-2.5 py-1.5 text-sm text-muted hover:bg-cloud hover:text-ink transition-colors">
          {{ chatOpen() ? 'Hide buddy' : 'Diary buddy' }}
        </button>
        <div class="rounded-lg bg-cloud/60 p-0.5 flex text-sm">
          <button type="button" (click)="mode.set('write')" [class]="mode() === 'write' ? 'rounded-md bg-white px-3 py-1 font-medium text-ink shadow-sm' : 'px-3 py-1 text-muted'">Write</button>
          <button type="button" (click)="mode.set('preview')" [class]="mode() === 'preview' ? 'rounded-md bg-white px-3 py-1 font-medium text-ink shadow-sm' : 'px-3 py-1 text-muted'">Preview</button>
        </div>
      </div>
    </div>

    @if (loading()) {
      <p class="text-muted mt-8">Opening your diary&hellip;</p>
    } @else {
      <!-- The diary page -->
      <div
        class="mx-auto mt-6 max-w-2xl rounded-2xl border shadow-sm overflow-hidden"
        [style.background]="theme().background"
        [style.color]="theme().ink"
        [style.borderColor]="theme().swatch"
        [style.fontFamily]="theme().fontFamily"
      >
        <div class="p-6 sm:p-10">
          <p class="text-2xl sm:text-3xl" [style.color]="theme().accent" [style.fontFamily]="theme().fontFamily">
            {{ dateHeader() }}
          </p>

          @if (featureImageUrl()) {
            <div class="mt-4">
              <img [src]="featureImageUrl()" alt="Diary photo" class="w-full max-h-80 object-cover rounded-xl" />
            </div>
          }

          @if (mode() === 'write') {
            <div class="mt-5">
              <app-editor-toolbar [activeMarks]="activeMarks()" (command)="onCommand($event)" />
              <div #editorEl class="markdown-content mt-2 min-h-[18rem]" [style.color]="theme().ink"></div>
            </div>
          } @else {
            <div class="markdown-content mt-5 min-h-[18rem]" [style.color]="theme().ink" [innerHTML]="renderedContent()"></div>
          }
        </div>
      </div>

      <!-- Theme picker -->
      <div class="mx-auto max-w-2xl mt-5">
        <p class="text-xs font-medium text-muted mb-2">Diary style</p>
        <div class="flex flex-wrap gap-2">
          @for (t of themes; track t.value) {
            <button
              type="button"
              (click)="selectTheme(t.value)"
              [class]="t.value === themeKey()
                ? 'flex items-center gap-2 rounded-xl border-2 border-moss bg-white px-3 py-2 text-sm shadow-sm'
                : 'flex items-center gap-2 rounded-xl border border-cloud bg-white px-3 py-2 text-sm hover:border-moss/60 transition-colors'"
              [title]="t.description"
            >
              <span class="h-4 w-4 rounded-full border border-black/10" [style.background]="t.swatch"></span>
              <span class="text-ink">{{ t.label }}</span>
            </button>
          }
        </div>
      </div>

      <!-- Actions -->
      <div class="mx-auto max-w-2xl mt-5 flex flex-wrap items-center gap-3">
        <label class="rounded-xl border border-cloud bg-paper px-4 py-2 text-sm font-medium text-ink hover:border-moss transition-colors cursor-pointer">
          {{ uploadingImage() ? 'Uploading…' : (featureImageUrl() ? 'Change photo' : 'Add a photo') }}
          <input type="file" accept="image/*" class="hidden" [disabled]="uploadingImage()" (change)="onPhotoSelected($event)" />
        </label>
        @if (featureImageUrl()) {
          <button type="button" (click)="removePhoto()" class="rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
            Remove photo
          </button>
        }

        <span class="flex-1"></span>

        @if (published()) {
          <span class="text-sm text-moss-dark font-medium">Shared to your blog</span>
        } @else if (submitted()) {
          <span class="text-sm text-muted">Waiting for a grown-up to approve</span>
        } @else {
          <button type="button" (click)="share()" [disabled]="sharing()" class="rounded-xl border border-cloud bg-paper px-4 py-2 text-sm font-medium text-ink hover:border-moss transition-colors disabled:opacity-60">
            {{ sharing() ? 'Sharing…' : (family.hasAcceptedGuardian() ? 'Share to blog (ask a grown-up)' : 'Share to blog') }}
          </button>
        }
      </div>
      @if (error()) {
        <p class="mx-auto max-w-2xl text-amber text-sm mt-2">{{ error() }}</p>
      }
    }

    <!-- Notes drawer (left) -->
    @if (notesOpen()) {
      <div class="fixed inset-0 z-40 bg-ink/20" (click)="notesOpen.set(false)"></div>
      <div class="fixed inset-y-0 left-0 z-50 w-full sm:w-80 bg-paper border-r border-cloud shadow-lg p-4 flex flex-col">
        <button type="button" (click)="notesOpen.set(false)" class="self-start rounded-lg px-3 py-1.5 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors mb-2">Close</button>
        <div class="flex-1 min-h-0">
          <app-notes-panel [body]="noteBody()" [status]="null" (bodyChange)="noteBody.set($event)" (blurred)="saveNote()" />
        </div>
      </div>
    }

    <!-- Diary buddy drawer (right) -->
    @if (chatOpen()) {
      <div class="fixed inset-0 z-40 bg-ink/20" (click)="chatOpen.set(false)"></div>
      <div class="fixed inset-y-0 right-0 z-50 w-full sm:w-96 bg-paper border-l border-cloud shadow-lg p-4 flex flex-col">
        <button type="button" (click)="chatOpen.set(false)" class="self-end rounded-lg px-3 py-1.5 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors mb-2">Close</button>
        <div class="flex-1 min-h-0">
          <app-companion-panel [contentId]="postId" [sessionId]="companionSessionId" />
        </div>
      </div>
    }
  `,
})
export default class DiaryEditorComponent implements OnInit, OnDestroy {
  private readonly blog = inject(BlogService);
  private readonly diary = inject(DiaryService);
  private readonly noteService = inject(NoteService);
  private readonly http = inject(HttpClient);
  private readonly route = inject(ActivatedRoute);
  readonly family = inject(FamilyService);

  private readonly editorEl = viewChild<{ nativeElement: HTMLElement }>('editorEl');

  readonly postId = this.route.snapshot.paramMap.get('id')!;
  readonly companionSessionId = crypto.randomUUID();
  readonly themes = DIARY_THEME_LIST;

  readonly loading = signal(true);
  readonly mode = signal<'write' | 'preview'>('write');
  readonly notesOpen = signal(false);
  readonly chatOpen = signal(false);

  readonly themeKey = signal<DiaryThemeKey>('classic');
  readonly theme = computed(() => resolveDiaryTheme(this.themeKey()));
  private readonly entryDate = signal<string | null>(null);
  readonly featureImageUrl = signal<string | undefined>(undefined);
  readonly noteBody = signal('');
  readonly autosaveStatus = signal<string | null>(null);
  readonly uploadingImage = signal(false);
  readonly sharing = signal(false);
  readonly published = signal(false);
  readonly submitted = signal(false);
  readonly error = signal<string | null>(null);

  readonly activeMarks = signal<Set<string>>(new Set());
  private readonly markdown = signal('');
  readonly renderedContent = computed(() => marked.parse(this.markdown(), { async: false }) as string);

  readonly dateHeader = computed(() => {
    const iso = this.entryDate();
    if (!iso) return '';
    // Parse as a local date (avoid the UTC shift of `new Date('YYYY-MM-DD')`).
    const [y, m, d] = iso.split('-').map(Number);
    return new Date(y, m - 1, d).toLocaleDateString(undefined, {
      weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
    });
  });

  private editor?: Editor;
  private seed = '';
  private autosaveTimer?: ReturnType<typeof setTimeout>;

  constructor() {
    effect(() => {
      const el = this.editorEl();
      if (el && this.mode() === 'write' && !this.editor && !this.loading()) {
        this.mountEditor(el.nativeElement);
      }
    });
  }

  async ngOnInit(): Promise<void> {
    const post = await this.blog.getById(this.postId);
    if (!post) {
      this.error.set('Could not open this diary entry.');
      this.loading.set(false);
      return;
    }
    this.entryDate.set(post.entry_date);
    this.themeKey.set((post.diary_theme as DiaryThemeKey) ?? 'classic');
    this.featureImageUrl.set(post.feature_image_url ?? undefined);
    this.seed = post.content_markdown;
    this.markdown.set(post.content_markdown);
    this.published.set(post.status === 'published');
    this.submitted.set(post.status === 'pending_review');

    const note = await this.noteService.getOrCreateForContent(this.postId);
    this.noteBody.set(note.body);
    this.loading.set(false);
  }

  ngOnDestroy(): void {
    if (this.autosaveTimer) clearTimeout(this.autosaveTimer);
    this.editor?.destroy();
  }

  private mountEditor(element: HTMLElement): void {
    this.editor = new Editor({
      element,
      extensions: [StarterKit, Markdown, Placeholder.configure({ placeholder: DIARY_PLACEHOLDER })],
      content: this.seed,
      contentType: 'markdown',
      onUpdate: () => {
        this.syncActiveMarks();
        this.markdown.set(this.editor?.getMarkdown() ?? '');
        this.scheduleAutosave();
      },
      onSelectionUpdate: () => this.syncActiveMarks(),
    });
    this.syncActiveMarks();
  }

  private syncActiveMarks(): void {
    if (!this.editor) return;
    this.activeMarks.set(computeActiveMarks(this.editor));
  }

  onCommand(command: ToolbarCommand): void {
    if (this.editor) applyToolbarCommand(this.editor, command);
  }

  async selectTheme(key: DiaryThemeKey): Promise<void> {
    if (key === this.themeKey()) return;
    this.themeKey.set(key);
    try {
      await this.blog.update(this.postId, { diary_theme: key });
    } catch {
      this.error.set('Could not save the diary style.');
    }
  }

  private scheduleAutosave(): void {
    if (this.autosaveTimer) clearTimeout(this.autosaveTimer);
    this.autosaveTimer = setTimeout(() => void this.autosave(), AUTOSAVE_DELAY_MS);
  }

  private async autosave(): Promise<void> {
    try {
      await this.blog.update(this.postId, { content_markdown: this.markdown() });
      this.autosaveStatus.set(`Autosaved ${new Date().toLocaleTimeString()}`);
    } catch {
      this.autosaveStatus.set('Autosave failed');
    }
  }

  async saveNote(): Promise<void> {
    await this.noteService.updateForContent(this.postId, this.noteBody());
  }

  async onPhotoSelected(event: Event): Promise<void> {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    this.uploadingImage.set(true);
    this.error.set(null);
    try {
      const blob = await resizeAndCompressImage(file);
      const formData = new FormData();
      formData.append('file', blob, 'diary-photo.jpg');
      const response = await firstValueFrom(this.http.post<{ url: string }>('/api/v1/uploads/feature-image', formData));
      this.featureImageUrl.set(response.url);
      await this.blog.update(this.postId, { feature_image_url: response.url });
    } catch {
      this.error.set('Photo upload failed. Please try again.');
    } finally {
      this.uploadingImage.set(false);
    }
  }

  async removePhoto(): Promise<void> {
    this.featureImageUrl.set(undefined);
    await this.blog.update(this.postId, { feature_image_url: '' });
  }

  async share(): Promise<void> {
    this.sharing.set(true);
    this.error.set(null);
    try {
      // Persist the latest text first, then run it through the same guardian
      // gate the blog uses: a linked grown-up must approve, otherwise it
      // self-publishes.
      await this.blog.update(this.postId, { content_markdown: this.markdown() });
      if (this.family.hasAcceptedGuardian()) {
        await this.blog.submitForReview(this.postId);
        this.submitted.set(true);
      } else {
        await this.blog.selfPublish(this.postId);
        this.published.set(true);
      }
    } catch (err) {
      const detail = (err as { error?: { detail?: string } })?.error?.detail;
      this.error.set(detail ?? 'Could not share this entry. Please try again.');
    } finally {
      this.sharing.set(false);
    }
  }
}
