import { Component, EventEmitter, Input, Output } from '@angular/core';

/**
 * Dumb, reused by the Topic reader and Writing Studio (@Input/@Output only,
 * no service injection — the parent owns the get-or-create + autosave
 * lifecycle, same split as JournalService vs. journal-entry.component.ts).
 * Always visible, never a modal/accordion — see docs/rowling-room-spec.md.
 */
@Component({
  selector: 'app-notes-panel',
  standalone: true,
  template: `
    <div class="rounded-2xl border border-cloud bg-white shadow-sm p-4 flex flex-col gap-2 h-full">
      <div class="flex items-baseline justify-between gap-2">
        <span class="text-sm font-medium text-muted">Your notes</span>
        @if (status) {
          <span class="text-xs text-muted font-mono">{{ status }}</span>
        }
      </div>
      <textarea
        rows="10"
        placeholder="Scribble key points as you go..."
        [value]="body"
        (input)="bodyChange.emit($any($event.target).value)"
        (blur)="blurred.emit()"
        class="flex-1 rounded-xl border border-cloud bg-paper px-3 py-2.5 leading-relaxed resize-y focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors"
      ></textarea>
    </div>
  `,
})
export class NotesPanelComponent {
  @Input() body = '';
  @Input() status: string | null = null;
  @Output() bodyChange = new EventEmitter<string>();
  @Output() blurred = new EventEmitter<void>();
}
