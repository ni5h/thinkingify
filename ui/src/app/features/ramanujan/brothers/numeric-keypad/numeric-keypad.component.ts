import { Component, EventEmitter, Input, Output } from '@angular/core';

/**
 * A dumb 0–9 keypad with clear + enter. @Input/@Output only — the parent
 * owns the current value and what "enter" does. Net-new; nothing like it
 * existed (Kakooma is tap-a-tile, and no other feature types numbers).
 */
@Component({
  selector: 'app-numeric-keypad',
  standalone: true,
  template: `
    <div class="grid grid-cols-3 gap-2 max-w-[15rem]">
      @for (key of digits; track key) {
        <button
          type="button"
          (click)="digit.emit(key)"
          [disabled]="disabled"
          class="rounded-xl border border-cloud bg-white shadow-sm py-3 font-display text-xl text-ink hover:border-moss hover:bg-cloud/40 transition-colors disabled:opacity-50"
        >
          {{ key }}
        </button>
      }
      <button
        type="button"
        (click)="clear.emit()"
        [disabled]="disabled"
        class="rounded-xl border border-cloud bg-paper py-3 text-sm font-medium text-muted hover:border-amber hover:text-amber transition-colors disabled:opacity-50"
      >
        Clear
      </button>
      <button
        type="button"
        (click)="digit.emit('0')"
        [disabled]="disabled"
        class="rounded-xl border border-cloud bg-white shadow-sm py-3 font-display text-xl text-ink hover:border-moss hover:bg-cloud/40 transition-colors disabled:opacity-50"
      >
        0
      </button>
      <button
        type="button"
        (click)="enter.emit()"
        [disabled]="disabled || !canSubmit"
        class="rounded-xl bg-moss py-3 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors disabled:opacity-50"
      >
        Enter
      </button>
    </div>
  `,
})
export class NumericKeypadComponent {
  readonly digits = ['1', '2', '3', '4', '5', '6', '7', '8', '9'];

  @Input() disabled = false;
  @Input() canSubmit = false;
  @Output() digit = new EventEmitter<string>();
  @Output() clear = new EventEmitter<void>();
  @Output() enter = new EventEmitter<void>();
}
