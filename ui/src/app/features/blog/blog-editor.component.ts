import { AfterViewInit, Component, OnDestroy, inject, signal, viewChild } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Editor } from '@tiptap/core';
import { StarterKit } from '@tiptap/starter-kit';
import { Markdown } from '@tiptap/markdown';
import { Placeholder } from '@tiptap/extension-placeholder';
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
        <span class="text-sm font-medium text-muted">Content</span>

        <div class="flex flex-wrap gap-3 border border-cloud border-b-0 px-3 py-2 bg-paper">
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

        <div #editorEl class="markdown-content border border-cloud px-4 py-3 min-h-[16rem]"></div>
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
export default class BlogEditorComponent implements AfterViewInit, OnDestroy {
  private readonly blog = inject(BlogService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  private readonly editorEl = viewChild<{ nativeElement: HTMLElement }>('editorEl');

  readonly postId = this.route.snapshot.paramMap.get('id') ?? undefined;

  private readonly existingPost = this.postId ? this.blog.getById(this.postId) : undefined;

  readonly title = signal(this.existingPost?.title ?? '');
  readonly tagline = signal(this.existingPost?.tagline ?? '');
  readonly coverImageDataUrl = signal<string | undefined>(this.existingPost?.coverImageDataUrl);

  private readonly activeMarks = signal<Set<string>>(new Set());

  private editor!: Editor;

  ngAfterViewInit(): void {
    this.editor = new Editor({
      element: this.editorEl()!.nativeElement,
      extensions: [
        StarterKit.configure({ link: { openOnClick: false } }),
        Markdown,
        Placeholder.configure({ placeholder: 'Start writing...' }),
      ],
      content: this.existingPost?.contentMarkdown ?? '',
      contentType: 'markdown',
      onUpdate: () => this.syncActiveMarks(),
      onSelectionUpdate: () => this.syncActiveMarks(),
    });
    this.syncActiveMarks();
  }

  ngOnDestroy(): void {
    this.editor?.destroy();
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
    return active ? 'text-sm text-ink border-b border-ink' : 'text-sm text-muted border-b border-transparent hover:border-muted';
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

  async onCoverImageSelected(event: Event): Promise<void> {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    this.coverImageDataUrl.set(await resizeAndCompressImage(file));
  }

  save(): void {
    const draft = {
      title: this.title(),
      tagline: this.tagline(),
      contentMarkdown: this.editor.getMarkdown(),
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
