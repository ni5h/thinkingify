import { Component, EventEmitter, Input, Output } from '@angular/core';
import { ToolbarCommand } from './apply-toolbar-command';

/**
 * Dumb toolbar for a TipTap editor — extracted so it isn't reimplemented
 * per section-editor instance. The caller owns the Editor and applies
 * commands via applyToolbarCommand()/computeActiveMarks() (same file as
 * ToolbarCommand) so this component never touches TipTap directly.
 */
@Component({
  selector: 'app-editor-toolbar',
  standalone: true,
  template: `
    <div class="flex flex-wrap items-center gap-1 rounded-t-xl border border-cloud border-b-0 px-3 py-2 bg-paper">
      <button type="button" (click)="command.emit('bold')" [class]="markClass('bold')">B</button>
      <button type="button" (click)="command.emit('italic')" [class]="markClass('italic')">I</button>
      <button type="button" (click)="command.emit('heading2')" [class]="markClass('heading2')">H2</button>
      <button type="button" (click)="command.emit('heading3')" [class]="markClass('heading3')">H3</button>
      <button type="button" (click)="command.emit('bulletList')" [class]="markClass('bulletList')">&bull; List</button>
      <button type="button" (click)="command.emit('orderedList')" [class]="markClass('orderedList')">1. List</button>
      <button type="button" (click)="command.emit('blockquote')" [class]="markClass('blockquote')">Quote</button>
    </div>
  `,
})
export class EditorToolbarComponent {
  @Input() activeMarks: Set<string> = new Set();
  @Output() command = new EventEmitter<ToolbarCommand>();

  markClass(name: string): string {
    const active = this.activeMarks.has(name);
    return active
      ? 'rounded-lg bg-moss/10 px-2.5 py-1.5 text-sm font-medium text-moss-dark'
      : 'rounded-lg px-2.5 py-1.5 text-sm text-muted hover:bg-cloud hover:text-ink transition-colors';
  }
}
