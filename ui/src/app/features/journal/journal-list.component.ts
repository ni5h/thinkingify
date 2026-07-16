import { Component, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { JournalService } from '../../core/services/journal.service';
import { JournalEntry } from '../../core/models';

const SNIPPET_LENGTH = 140;

@Component({
  selector: 'app-journal-list',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    <div class="flex items-baseline justify-between gap-4">
      <h1 class="font-display text-3xl">Journal</h1>
      <a routerLink="/journal/new" class="rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors">
        New entry
      </a>
    </div>

    @if (entries().length === 0) {
      <p class="text-muted mt-6">No entries yet. Start your first one.</p>
    } @else {
      <ul class="mt-8 flex flex-col gap-4">
        @for (entry of entries(); track entry.id) {
          <li class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
            <div class="flex items-start justify-between gap-4">
              <div>
                <h2 class="font-display text-xl text-ink">{{ entry.title || '(untitled entry)' }}</h2>
                <p class="text-muted text-sm mt-1">{{ snippet(entry) }}</p>
                <p class="text-xs text-muted font-mono mt-2">{{ entry.date | date: 'mediumDate' }}</p>
              </div>
            </div>

            <div class="flex flex-wrap gap-2 mt-4">
              <a [routerLink]="['/journal', entry.id]" class="rounded-lg bg-cloud px-3 py-1.5 text-sm font-medium text-ink hover:bg-cloud/80 transition-colors">
                Open entry
              </a>
              <button type="button" (click)="remove(entry.id)" class="rounded-lg px-3 py-1.5 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
                Delete
              </button>
            </div>
          </li>
        }
      </ul>
    }
  `,
})
export default class JournalListComponent {
  private readonly journal = inject(JournalService);

  readonly entries = this.journal.entries;

  snippet(entry: JournalEntry): string {
    const text = entry.whatILearned.trim();
    if (!text) return '';
    return text.length > SNIPPET_LENGTH ? `${text.slice(0, SNIPPET_LENGTH)}…` : text;
  }

  remove(id: string): void {
    if (confirm('Delete this entry for good?')) {
      this.journal.delete(id);
    }
  }
}
