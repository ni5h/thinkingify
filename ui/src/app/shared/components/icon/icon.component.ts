import { Component, Input } from '@angular/core';

export type IconName =
  | 'home'
  | 'puzzle'
  | 'learn'
  | 'rowling'
  | 'sherlock'
  | 'progress'
  | 'menu'
  | 'arrow-right'
  | 'play'
  | 'pause'
  | 'user'
  | 'settings'
  | 'log-in';

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
      @case ('rowling') {
        <svg [attr.width]="size" [attr.height]="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14.5 4.5 19 9l-9 9-5 1 1-5 8.5-9.5Z" />
          <path d="M13 6l4 4" />
        </svg>
      }
      @case ('sherlock') {
        <svg [attr.width]="size" [attr.height]="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="10.5" cy="10.5" r="6" />
          <path d="M15 15l5.5 5.5" />
        </svg>
      }
      @case ('progress') {
        <svg [attr.width]="size" [attr.height]="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 16 10 10l4 3 6-7" />
          <path d="M16 6h4v4" />
        </svg>
      }
      @case ('menu') {
        <svg [attr.width]="size" [attr.height]="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 7h16M4 12h16M4 17h16" />
        </svg>
      }
      @case ('arrow-right') {
        <svg [attr.width]="size" [attr.height]="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 12h16M13 5l7 7-7 7" />
        </svg>
      }
      @case ('play') {
        <svg [attr.width]="size" [attr.height]="size" viewBox="0 0 24 24" fill="currentColor" stroke="none">
          <path d="M7 5v14l12-7Z" />
        </svg>
      }
      @case ('pause') {
        <svg [attr.width]="size" [attr.height]="size" viewBox="0 0 24 24" fill="currentColor" stroke="none">
          <rect x="6" y="5" width="4" height="14" rx="1" />
          <rect x="14" y="5" width="4" height="14" rx="1" />
        </svg>
      }
      @case ('user') {
        <svg [attr.width]="size" [attr.height]="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="8" r="3.5" />
          <path d="M4.5 20c1.3-3.5 4.3-5.5 7.5-5.5s6.2 2 7.5 5.5" />
        </svg>
      }
      @case ('settings') {
        <svg [attr.width]="size" [attr.height]="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 13.5a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1 1.55V19.5a2 2 0 1 1-4 0v-.09a1.7 1.7 0 0 0-1-1.56 1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.7 1.7 0 0 0 .34-1.87 1.7 1.7 0 0 0-1.55-1H4.5a2 2 0 1 1 0-4h.09a1.7 1.7 0 0 0 1.56-1 1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.7 1.7 0 0 0 1.87.34H10.5a1.7 1.7 0 0 0 1-1.55V4.5a2 2 0 1 1 4 0v.09a1.7 1.7 0 0 0 1 1.56 1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.7 1.7 0 0 0-.34 1.87V10.5a1.7 1.7 0 0 0 1.55 1H19.5a2 2 0 1 1 0 4h-.09a1.7 1.7 0 0 0-1.56 1Z" />
        </svg>
      }
      @case ('log-in') {
        <svg [attr.width]="size" [attr.height]="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path d="M13 4h4a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1h-4" />
          <path d="M10 8l4 4-4 4" />
          <path d="M14 12H3" />
        </svg>
      }
    }
  `,
})
export class IconComponent {
  @Input({ required: true }) name!: IconName;
  @Input() size = 20;
}
