import { Component, Input } from '@angular/core';

export type IconName = 'home' | 'puzzle' | 'learn' | 'journal' | 'blog' | 'progress';

@Component({
  selector: 'app-icon',
  standalone: true,
  template: `
    @switch (name) {
      @case ('home') {
        <svg [attr.width]="size" [attr.height]="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 11.5 12 4l9 7.5" />
          <path d="M5.5 10v9a1 1 0 0 0 1 1H9.5v-5a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v5h3a1 1 0 0 0 1-1v-9" />
        </svg>
      }
      @case ('puzzle') {
        <svg [attr.width]="size" [attr.height]="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 4.5h3a1.5 1.5 0 1 1 0 3H19.5v3a1.5 1.5 0 1 0 0 3v3a1.5 1.5 0 1 1-3 0h-3a1.5 1.5 0 1 1 0-3v-3H9a1.5 1.5 0 1 0 0-3h-4.5v12h3" />
        </svg>
      }
      @case ('learn') {
        <svg [attr.width]="size" [attr.height]="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 6.5c-1.8-1.2-4.2-1.7-6.5-1.2v12c2.3-.5 4.7 0 6.5 1.2 1.8-1.2 4.2-1.7 6.5-1.2v-12c-2.3-.5-4.7 0-6.5 1.2Z" />
          <path d="M12 6.5v12" />
        </svg>
      }
      @case ('journal') {
        <svg [attr.width]="size" [attr.height]="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <rect x="5" y="3.5" width="14" height="17" rx="1.5" />
          <path d="M9 8h6M9 12h6M9 16h4" />
        </svg>
      }
      @case ('blog') {
        <svg [attr.width]="size" [attr.height]="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14.5 4.5 19 9l-9 9-5 1 1-5 8.5-9.5Z" />
          <path d="M13 6l4 4" />
        </svg>
      }
      @case ('progress') {
        <svg [attr.width]="size" [attr.height]="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 16 10 10l4 3 6-7" />
          <path d="M16 6h4v4" />
        </svg>
      }
    }
  `,
})
export class IconComponent {
  @Input({ required: true }) name!: IconName;
  @Input() size = 20;
}
