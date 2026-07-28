import { AfterViewInit, Component, EventEmitter, Input, OnDestroy, Output, signal, viewChild } from '@angular/core';
import { Editor } from '@tiptap/core';
import { StarterKit } from '@tiptap/starter-kit';
import { Markdown } from '@tiptap/markdown';
import { Placeholder } from '@tiptap/extension-placeholder';
import { EditorToolbarComponent } from '../../../../shared/components/editor-toolbar/editor-toolbar.component';
import { applyToolbarCommand, computeActiveMarks, ToolbarCommand } from '../../../../shared/components/editor-toolbar/apply-toolbar-command';
import { ScaffoldSection } from '../style-scaffolds';

/**
 * One writing section's own small TipTap instance — a scaffolded style's
 * writing area is N of these stacked, not one shared editor. Keeps the
 * persistent label/example UI simple Angular template chrome rather than
 * needing ProseMirror decorations/NodeViews inside a shared document.
 */
@Component({
  selector: 'app-section-editor',
  standalone: true,
  imports: [EditorToolbarComponent],
  template: `
    <div class="rounded-2xl border border-cloud bg-white shadow-sm p-4">
      <div class="flex items-center justify-between gap-2">
        <span class="text-sm font-medium text-ink">{{ section.label }}</span>
        <button
          type="button"
          (click)="showExample.set(!showExample())"
          class="rounded-lg px-2 py-1 text-xs font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors"
        >
          💡 {{ showExample() ? 'Hide example' : 'Show example' }}
        </button>
      </div>

      @if (showExample()) {
        <p class="rounded-xl bg-cloud/40 p-3 text-sm text-muted mt-2 whitespace-pre-line">{{ section.example }}</p>
      }

      <div class="mt-3">
        <app-editor-toolbar [activeMarks]="activeMarks()" (command)="onCommand($event)" />
        <div #editorEl class="markdown-content rounded-b-xl border border-cloud px-4 py-3 min-h-[8rem] focus-within:border-moss transition-colors"></div>
      </div>
    </div>
  `,
})
export class SectionEditorComponent implements AfterViewInit, OnDestroy {
  @Input({ required: true }) section!: ScaffoldSection;
  @Input() initialMarkdown = '';
  @Output() markdownChange = new EventEmitter<string>();

  readonly showExample = signal(false);
  readonly activeMarks = signal<Set<string>>(new Set());

  private readonly editorEl = viewChild<{ nativeElement: HTMLElement }>('editorEl');
  private editor!: Editor;

  ngAfterViewInit(): void {
    this.editor = new Editor({
      element: this.editorEl()!.nativeElement,
      extensions: [StarterKit, Markdown, Placeholder.configure({ placeholder: this.section.prompt })],
      content: this.initialMarkdown,
      contentType: 'markdown',
      onUpdate: () => {
        this.syncActiveMarks();
        this.markdownChange.emit(this.editor.getMarkdown());
      },
      onSelectionUpdate: () => this.syncActiveMarks(),
    });
    this.syncActiveMarks();
  }

  ngOnDestroy(): void {
    this.editor?.destroy();
  }

  /** Called by the parent right after revealing this section. */
  focusEditor(): void {
    this.editor?.commands.focus('end');
  }

  private syncActiveMarks(): void {
    // Seeding non-trivial initial content can trigger onUpdate synchronously
    // during `new Editor(...)`, before `this.editor` is assigned — same
    // quirk as the original single-editor writing studio, same guard.
    if (!this.editor) return;
    this.activeMarks.set(computeActiveMarks(this.editor));
  }

  onCommand(command: ToolbarCommand): void {
    applyToolbarCommand(this.editor, command);
  }
}
