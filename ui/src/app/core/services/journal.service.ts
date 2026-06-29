import { Injectable, computed, inject } from '@angular/core';
import { StorageService } from './storage.service';
import { JournalEntry } from '../models';

export type JournalDraft = Omit<JournalEntry, 'id' | 'date'>;

@Injectable({ providedIn: 'root' })
export class JournalService {
  private readonly storage = inject(StorageService);

  readonly entries = computed(() =>
    [...this.storage.state().journalEntries].sort((a, b) => b.date.localeCompare(a.date))
  );

  getById(id: string): JournalEntry | undefined {
    return this.storage.state().journalEntries.find((entry) => entry.id === id);
  }

  create(draft: JournalDraft): JournalEntry {
    const entry: JournalEntry = {
      ...draft,
      id: crypto.randomUUID(),
      date: new Date().toISOString().slice(0, 10),
    };
    this.storage.update((state) => ({
      ...state,
      journalEntries: [...state.journalEntries, entry],
    }));
    this.storage.recordActivityToday();
    return entry;
  }

  update(id: string, changes: Partial<JournalDraft>): void {
    this.storage.update((state) => ({
      ...state,
      journalEntries: state.journalEntries.map((entry) =>
        entry.id === id ? { ...entry, ...changes } : entry
      ),
    }));
    this.storage.recordActivityToday();
  }

  delete(id: string): void {
    this.storage.update((state) => ({
      ...state,
      journalEntries: state.journalEntries.filter((entry) => entry.id !== id),
    }));
  }
}
