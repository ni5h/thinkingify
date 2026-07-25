import { AfterViewInit, Component, OnDestroy, inject, signal, viewChild } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Editor } from '@tiptap/core';
import { StarterKit } from '@tiptap/starter-kit';
import { Markdown } from '@tiptap/markdown';
import { Placeholder } from '@tiptap/extension-placeholder';
import { Image } from '@tiptap/extension-image';
import { TopicService } from '../../../core/services/topic.service';
import { TOPIC_THEMES } from '../../../core/models/theme';

const AUTOSAVE_DELAY_MS = 3000;

@Component({
  selector: 'app-topic-editor',
  standalone: true,
  imports: [RouterLink],
  template: `
    <a routerLink="/studio/topics" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
      &larr; Back to topics
    </a>

    <div class="flex items-baseline justify-between gap-4 mt-4">
      <h1 class="font-display text-3xl">{{ topicId ? 'Edit Topic' : 'New Topic' }}</h1>
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
        <span class="text-sm font-medium text-muted">Order (lower shows first)</span>
        <input
          type="number"
          [value]="orderIndex()"
          (input)="onOrderIndexInput($any($event.target).value)"
          class="rounded-xl border border-cloud bg-paper px-3 py-2.5 w-32 focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors"
        />
      </label>

      <label class="flex flex-col gap-1">
        <span class="text-sm font-medium text-muted">Audio narration — required to publish</span>
        <input type="file" accept="audio/*" [disabled]="uploadingAudio()" (change)="onAudioSelected($event)" />
        @if (uploadingAudio()) {
          <p class="text-xs text-muted mt-1">Uploading…</p>
        }
        @if (audioUrl()) {
          <audio [src]="audioUrl()" controls class="mt-2"></audio>
        }
      </label>

      <div class="flex flex-col gap-2">
        <span class="text-sm font-medium text-muted">Themes — at least one required to publish</span>
        <div class="flex flex-wrap gap-2">
          @for (theme of themeCatalog; track theme.slug) {
            <button
              type="button"
              (click)="toggleTheme(theme.slug)"
              [class]="themes().includes(theme.slug)
                ? 'rounded-lg bg-moss/10 px-3 py-1.5 text-sm font-medium text-moss-dark border border-moss/30'
                : 'rounded-lg px-3 py-1.5 text-sm text-muted border border-cloud hover:bg-cloud/60 hover:text-ink transition-colors'"
            >
              {{ theme.label }}
            </button>
          }
        </div>
      </div>

      <div class="flex flex-col gap-1">
        <span class="text-sm font-medium text-muted">Explainer</span>

        <div class="flex flex-wrap gap-1 rounded-t-xl border border-cloud border-b-0 px-3 py-2 bg-paper">
          <button type="button" (click)="toggleBold()" [class]="markClass('bold')">B</button>
          <button type="button" (click)="toggleItalic()" [class]="markClass('italic')">I</button>
          <button type="button" (click)="toggleHeading(2)" [class]="markClass('heading2')">H2</button>
          <button type="button" (click)="toggleHeading(3)" [class]="markClass('heading3')">H3</button>
          <button type="button" (click)="toggleBulletList()" [class]="markClass('bulletList')">&bull; List</button>
          <button type="button" (click)="toggleBlockquote()" [class]="markClass('blockquote')">Quote</button>
          <button type="button" [disabled]="uploadingImage()" (click)="triggerImagePicker()" class="rounded-lg px-2.5 py-1.5 text-sm text-muted hover:bg-cloud hover:text-ink transition-colors disabled:opacity-60">
            {{ uploadingImage() ? 'Uploading…' : 'Image' }}
          </button>
          <input #imageInput type="file" accept="image/*" class="hidden" (change)="onInlineImageSelected($event)" />
        </div>

        <div #editorEl class="markdown-content rounded-b-xl border border-cloud px-4 py-3 min-h-[16rem] focus-within:border-moss transition-colors"></div>
      </div>

      <div class="flex flex-wrap gap-3 mt-2">
        <button type="button" (click)="save()" [disabled]="saving()" class="rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors disabled:opacity-60">
          {{ saving() ? 'Saving…' : 'Save' }}
        </button>
        @if (topicId && status() === 'draft') {
          <button
            type="button"
            (click)="publish()"
            [disabled]="!audioUrl() || themes().length === 0"
            class="rounded-xl border border-cloud bg-paper px-5 py-2.5 text-sm font-medium text-ink hover:border-moss hover:bg-cloud/60 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
          >
            Publish
          </button>
          @if (!audioUrl() || themes().length === 0) {
            <span class="text-xs text-muted self-center">
              @if (!audioUrl() && themes().length === 0) {
                Add audio and at least one theme before you can publish.
              } @else if (!audioUrl()) {
                Add audio above before you can publish.
              } @else {
                Add at least one theme before you can publish.
              }
            </span>
          }
        }
        @if (topicId && status() === 'published') {
          <button type="button" (click)="unpublish()" class="rounded-xl border border-cloud bg-paper px-5 py-2.5 text-sm font-medium text-ink hover:border-moss hover:bg-cloud/60 transition-colors">
            Unpublish
          </button>
        }
        <a routerLink="/studio/topics" class="rounded-xl px-5 py-2.5 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
          Cancel
        </a>
      </div>

      @if (error()) {
        <p class="text-amber text-sm">{{ error() }}</p>
      }
    </div>
  `,
})
export default class TopicEditorComponent implements AfterViewInit, OnDestroy {
  private readonly topicService = inject(TopicService);
  private readonly http = inject(HttpClient);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  private readonly editorEl = viewChild<{ nativeElement: HTMLElement }>('editorEl');
  private readonly imageInput = viewChild<{ nativeElement: HTMLInputElement }>('imageInput');

  readonly topicId = this.route.snapshot.paramMap.get('id') ?? undefined;

  readonly title = signal('');
  readonly orderIndex = signal(0);
  readonly audioUrl = signal<string | undefined>(undefined);
  readonly themes = signal<string[]>([]);
  readonly themeCatalog = TOPIC_THEMES;
  readonly status = signal<'draft' | 'published'>('draft');
  readonly uploadingAudio = signal(false);
  readonly uploadingImage = signal(false);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly autosaveStatus = signal<string | null>(null);

  private readonly activeMarks = signal<Set<string>>(new Set());

  private editor!: Editor;
  private autosaveTimer?: ReturnType<typeof setTimeout>;

  onOrderIndexInput(value: string): void {
    this.orderIndex.set(Number(value));
  }

  toggleTheme(slug: string): void {
    const set = new Set(this.themes());
    if (set.has(slug)) set.delete(slug);
    else set.add(slug);
    this.themes.set([...set]);
  }

  async ngAfterViewInit(): Promise<void> {
    let initialMarkdown = '';

    if (this.topicId) {
      const existing = await this.topicService.getById(this.topicId);
      if (existing) {
        this.title.set(existing.title);
        this.orderIndex.set(existing.order_index);
        this.audioUrl.set(existing.audio_url ?? undefined);
        this.themes.set(existing.themes);
        this.status.set(existing.status);
        initialMarkdown = existing.explainer_markdown;
      }
    }

    this.editor = new Editor({
      element: this.editorEl()!.nativeElement,
      extensions: [
        StarterKit,
        Markdown,
        Image,
        Placeholder.configure({ placeholder: 'Write the explainer...' }),
      ],
      content: initialMarkdown,
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

  private scheduleAutosave(): void {
    if (!this.topicId) return;
    if (this.autosaveTimer) clearTimeout(this.autosaveTimer);
    this.autosaveTimer = setTimeout(() => void this.autosave(), AUTOSAVE_DELAY_MS);
  }

  private async autosave(): Promise<void> {
    if (!this.topicId) return;
    try {
      await this.topicService.update(this.topicId, {
        title: this.title(),
        order_index: this.orderIndex(),
        audio_url: this.audioUrl(),
        themes: this.themes(),
        explainer_markdown: this.editor.getMarkdown(),
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
    if (this.editor.isActive('heading', { level: 2 })) active.add('heading2');
    if (this.editor.isActive('heading', { level: 3 })) active.add('heading3');
    if (this.editor.isActive('bulletList')) active.add('bulletList');
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

  toggleBlockquote(): void {
    this.editor.chain().focus().toggleBlockquote().run();
  }

  triggerImagePicker(): void {
    this.imageInput()?.nativeElement.click();
  }

  async onInlineImageSelected(event: Event): Promise<void> {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;

    this.uploadingImage.set(true);
    this.error.set(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await firstValueFrom(
        this.http.post<{ url: string }>('/api/v1/uploads/topic-image', formData)
      );
      this.editor.chain().focus().setImage({ src: response.url }).run();
    } catch {
      this.error.set('Image upload failed. Please try again.');
    } finally {
      this.uploadingImage.set(false);
      (event.target as HTMLInputElement).value = '';
    }
  }

  async onAudioSelected(event: Event): Promise<void> {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;

    this.uploadingAudio.set(true);
    this.error.set(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await firstValueFrom(
        this.http.post<{ url: string }>('/api/v1/uploads/topic-audio', formData)
      );
      this.audioUrl.set(response.url);
    } catch {
      this.error.set('Audio upload failed. Please try again.');
    } finally {
      this.uploadingAudio.set(false);
    }
  }

  async save(): Promise<void> {
    this.saving.set(true);
    this.error.set(null);
    try {
      const draft = {
        title: this.title(),
        order_index: this.orderIndex(),
        audio_url: this.audioUrl(),
        themes: this.themes(),
        explainer_markdown: this.editor.getMarkdown(),
      };

      if (this.topicId) {
        await this.topicService.update(this.topicId, draft);
      } else {
        await this.topicService.create(draft);
      }

      await this.router.navigate(['/studio/topics']);
    } catch {
      this.error.set('Could not save this topic. Please try again.');
      this.saving.set(false);
    }
  }

  async publish(): Promise<void> {
    if (!this.topicId) return;
    this.error.set(null);
    try {
      await this.topicService.publish(this.topicId);
      this.status.set('published');
    } catch (err) {
      const detail = (err as { error?: { detail?: string } })?.error?.detail;
      this.error.set(detail ?? 'Could not publish this topic. Please try again.');
    }
  }

  async unpublish(): Promise<void> {
    if (!this.topicId) return;
    await this.topicService.unpublish(this.topicId);
    this.status.set('draft');
  }
}
