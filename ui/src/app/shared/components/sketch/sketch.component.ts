import { Component, Input } from '@angular/core';

export type SketchName = 'circle-underline' | 'connecting-dots' | 'margin-arrow' | 'bracket';

/**
 * Purely decorative "notebook sketch" marks — distinct from IconComponent,
 * which is sometimes meaningful navigation. This component is never
 * navigational, so aria-hidden is baked into the template unconditionally
 * rather than left to the caller.
 */
@Component({
  selector: 'app-sketch',
  standalone: true,
  template: `
    @switch (name) {
      @case ('circle-underline') {
        <svg [attr.width]="width" [attr.height]="height" viewBox="0 0 160 60" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true" focusable="false">
          <path d="M8 34C8 34 34 14 80 12C126 10 152 26 150 34" />
          <path d="M10 38C34 52 128 52 152 36" />
        </svg>
      }
      @case ('connecting-dots') {
        <svg [attr.width]="width" [attr.height]="height" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" aria-hidden="true" focusable="false">
          <path d="M9 12L27 8M27 8L39 30M9 12L39 30" />
          <circle cx="9" cy="12" r="2.5" fill="currentColor" stroke="none" />
          <circle cx="27" cy="8" r="2.5" fill="currentColor" stroke="none" />
          <circle cx="39" cy="30" r="2.5" fill="currentColor" stroke="none" />
        </svg>
      }
      @case ('margin-arrow') {
        <svg [attr.width]="width" [attr.height]="height" viewBox="0 0 60 40" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
          <path d="M6 8C18 8 40 14 52 30" />
          <path d="M40 27L52 30L47 18" />
        </svg>
      }
      @case ('bracket') {
        <svg [attr.width]="width" [attr.height]="height" viewBox="0 0 24 120" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true" focusable="false">
          <path d="M18 4C10 4 6 10 6 20V50C6 58 2 60 2 60C2 60 6 62 6 70V100C6 110 10 116 18 116" />
        </svg>
      }
    }
  `,
})
export class SketchComponent {
  @Input({ required: true }) name!: SketchName;
  @Input() width = 48;
  @Input() height = 48;
}
