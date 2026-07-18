import { Component, ElementRef, Input, computed, signal, viewChild } from '@angular/core';
import { IconComponent } from '../icon/icon.component';

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds)) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Dumb custom-controls audio player — no native <audio controls> on
 * kid-facing screens (unstylable browser chrome breaks the warm/rounded
 * look). Built entirely from existing recipes: card, moss accent range
 * input, font-mono time readout. See ui/CLAUDE.md's Rooms IA section.
 */
@Component({
  selector: 'app-audio-player',
  standalone: true,
  imports: [IconComponent],
  template: `
    <div class="rounded-2xl border border-cloud bg-white shadow-sm p-4 flex items-center gap-4">
      <audio
        #audioEl
        [src]="src"
        (loadedmetadata)="duration.set(audioEl.duration)"
        (timeupdate)="currentTime.set(audioEl.currentTime)"
        (ended)="playing.set(false)"
        class="hidden"
      ></audio>

      <button
        type="button"
        (click)="togglePlay(audioEl)"
        [attr.aria-label]="playing() ? 'Pause' : 'Play'"
        class="shrink-0 flex items-center justify-center h-11 w-11 rounded-full bg-moss text-white shadow-sm hover:bg-moss-dark transition-colors"
      >
        <app-icon [name]="playing() ? 'pause' : 'play'" [size]="18" />
      </button>

      <input
        type="range"
        min="0"
        [max]="duration() || 0"
        [value]="currentTime()"
        (input)="seek(audioEl, $any($event.target).value)"
        class="flex-1 accent-moss"
      />

      <span class="text-xs text-muted font-mono shrink-0">{{ elapsedLabel() }} / {{ durationLabel() }}</span>
    </div>
  `,
})
export class AudioPlayerComponent {
  @Input({ required: true }) src!: string;

  private readonly audioElRef = viewChild<ElementRef<HTMLAudioElement>>('audioEl');

  readonly playing = signal(false);
  readonly currentTime = signal(0);
  readonly duration = signal(0);

  readonly elapsedLabel = computed(() => formatTime(this.currentTime()));
  readonly durationLabel = computed(() => formatTime(this.duration()));

  togglePlay(audioEl: HTMLAudioElement): void {
    if (this.playing()) {
      audioEl.pause();
    } else {
      void audioEl.play();
    }
    this.playing.set(!this.playing());
  }

  seek(audioEl: HTMLAudioElement, value: string): void {
    const time = Number(value);
    audioEl.currentTime = time;
    this.currentTime.set(time);
  }
}
