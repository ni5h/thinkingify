import { Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { IconComponent, IconName } from '../icon/icon.component';

export type RoomTone = 'ramanujan' | 'einstein' | 'rowling' | 'sherlock';

export interface RoomDoor {
  id: string;
  title: string;
  blurb: string;
  route: string | string[];
  icon?: IconName;
  /** The recommended next door gets a ringed border. */
  recommended?: boolean;
}

interface ToneStyle {
  color: string;
  tint: string;
}

const TONES: Record<RoomTone, ToneStyle> = {
  ramanujan: { color: '#14746F', tint: '#DDF1EE' },
  einstein: { color: '#2F5DA8', tint: '#E1EBF9' },
  rowling: { color: '#7B3F86', tint: '#F0E3F3' },
  sherlock: { color: '#94590C', tint: '#FBEBD0' },
};

const NEUTRAL_BORDER = '#D5DCE6';

/**
 * Shared room layout: a left column (title + a projected chapter list) and a
 * right column of "doors" (a 3-col grid) plus a projected "how it works" strip.
 * Tone drives the room accent via inline colors (so Tailwind's purge can't drop
 * dynamic class names). Only pass doors that exist; the recommended one is
 * ringed.
 */
@Component({
  selector: 'app-room-shell',
  standalone: true,
  imports: [RouterLink, IconComponent],
  template: `
    <div class="md:flex md:gap-8">
      <!-- Left: title + chapter list -->
      <aside class="md:w-72 md:shrink-0">
        <div class="flex items-center gap-3">
          <span class="h-10 w-10 rounded-xl flex items-center justify-center shrink-0" [style.background]="toneStyle().tint" [style.color]="toneStyle().color">
            <app-icon [name]="icon" [size]="22" />
          </span>
          <div>
            <h1 class="font-display text-2xl text-ink leading-tight">{{ roomName }}</h1>
            <p class="text-sm font-medium" [style.color]="toneStyle().color">{{ subjectLabel }}</p>
          </div>
        </div>
        <div class="mt-6">
          <ng-content select="[chapters]" />
        </div>
      </aside>

      <!-- Right: doors + how-it-works -->
      <div class="flex-1 min-w-0 mt-8 md:mt-0">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          @for (door of doors; track door.id) {
            <a
              [routerLink]="door.route"
              class="rounded-2xl border bg-white shadow-sm p-5 transition-shadow hover:shadow-md flex flex-col gap-2"
              [style.borderColor]="door.recommended ? toneStyle().color : neutralBorder"
              [style.borderWidth]="door.recommended ? '2px' : '1px'"
            >
              @if (door.icon) {
                <span class="h-9 w-9 rounded-xl flex items-center justify-center" [style.background]="toneStyle().tint" [style.color]="toneStyle().color">
                  <app-icon [name]="door.icon" [size]="20" />
                </span>
              }
              <h3 class="font-display text-lg text-ink mt-1">{{ door.title }}</h3>
              <p class="text-sm text-muted">{{ door.blurb }}</p>
              @if (door.recommended) {
                <span class="text-xs font-medium mt-1" [style.color]="toneStyle().color">Start here &rarr;</span>
              }
            </a>
          }
        </div>
        <div class="mt-6">
          <ng-content select="[howItWorks]" />
        </div>
      </div>
    </div>
  `,
})
export class RoomShellComponent {
  @Input({ required: true }) roomName!: string;
  @Input({ required: true }) subjectLabel!: string;
  @Input({ required: true }) tone!: RoomTone;
  @Input({ required: true }) icon!: IconName;
  @Input() doors: RoomDoor[] = [];

  readonly neutralBorder = NEUTRAL_BORDER;

  toneStyle(): ToneStyle {
    return TONES[this.tone];
  }
}
