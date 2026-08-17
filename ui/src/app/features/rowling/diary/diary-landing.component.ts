import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink, Router } from '@angular/router';
import { DiaryService } from '../../../core/services/diary.service';
import { ContentListItem } from '../../../core/models/content';
import { resolveDiaryTheme } from './diary-themes';

@Component({
  selector: 'app-diary-landing',
  standalone: true,
  imports: [RouterLink],
  template: `
    <a routerLink="/rowling" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
      &larr; Back to Rowling
    </a>

    <h1 class="font-display text-3xl mt-4">My Diary</h1>
    <p class="text-muted mt-2 max-w-prose">
      A quiet place to write about your day &mdash; what happened, how it felt, the little things
      worth remembering. Only you (and a grown-up you've linked) can read it.
    </p>

    <button
      type="button"
      (click)="writeToday()"
      [disabled]="opening()"
      class="mt-6 rounded-xl bg-moss px-6 py-3 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors disabled:opacity-60"
    >
      {{ opening() ? 'Opening…' : "Write today's entry" }}
    </button>
    @if (error()) {
      <p class="text-amber text-sm mt-3">{{ error() }}</p>
    }

    @if (entries().length > 0) {
      <h2 class="font-display text-xl mt-10">Past entries</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
        @for (entry of entries(); track entry.id) {
          <a
            [routerLink]="['/rowling/diary', entry.id]"
            class="rounded-2xl border border-cloud shadow-sm p-5 hover:shadow-md transition-shadow flex items-start gap-4"
            [style.background]="themeOf(entry).background"
            [style.borderColor]="themeOf(entry).swatch"
          >
            @if (entry.feature_image_url) {
              <img [src]="entry.feature_image_url" alt="" class="h-16 w-16 rounded-lg object-cover shrink-0" />
            } @else {
              <span class="h-16 w-16 rounded-lg shrink-0 border border-black/5" [style.background]="themeOf(entry).swatch"></span>
            }
            <div class="min-w-0">
              <p class="font-medium truncate" [style.color]="themeOf(entry).ink" [style.fontFamily]="themeOf(entry).fontFamily">
                {{ formatDate(entry.entry_date) }}
              </p>
              <p class="text-xs mt-1" [style.color]="themeOf(entry).accent">{{ themeOf(entry).label }}</p>
              @if (entry.status === 'published') {
                <span class="inline-block mt-2 rounded-lg bg-moss/10 px-2 py-0.5 text-xs font-medium text-moss-dark">on your blog</span>
              } @else if (entry.status === 'pending_review') {
                <span class="inline-block mt-2 rounded-lg bg-amber/10 px-2 py-0.5 text-xs font-medium text-amber">waiting for approval</span>
              }
            </div>
          </a>
        }
      </div>
    }
  `,
})
export default class DiaryLandingComponent implements OnInit {
  private readonly diary = inject(DiaryService);
  private readonly router = inject(Router);

  readonly entries = signal<ContentListItem[]>([]);
  readonly opening = signal(false);
  readonly error = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    try {
      this.entries.set(await this.diary.list());
    } catch {
      // Non-critical — the "write today" button still works.
    }
  }

  themeOf(entry: ContentListItem) {
    return resolveDiaryTheme(entry.diary_theme);
  }

  formatDate(iso: string | null): string {
    if (!iso) return '(undated)';
    const [y, m, d] = iso.split('-').map(Number);
    return new Date(y, m - 1, d).toLocaleDateString(undefined, {
      weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
    });
  }

  private localToday(): string {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, '0');
    const d = String(now.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }

  async writeToday(): Promise<void> {
    this.opening.set(true);
    this.error.set(null);
    try {
      const entry = await this.diary.today(this.localToday());
      await this.router.navigate(['/rowling/diary', entry.id]);
    } catch {
      this.error.set('Could not open your diary. Please try again.');
      this.opening.set(false);
    }
  }
}
