import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { Content, ContentListItem } from '../models/content';

/**
 * "My Diary" — one dated entry per day. Entries are Content rows
 * (style 'diary_entry'); the editor reuses BlogService.update for autosave,
 * theme, and photo. These two calls are diary-specific: resolving today's
 * entry (get-or-create) and listing past entries.
 */
@Injectable({ providedIn: 'root' })
export class DiaryService {
  private readonly http = inject(HttpClient);

  /** Get-or-create the entry for the given local date (YYYY-MM-DD). */
  async today(localDate: string): Promise<Content> {
    return firstValueFrom(this.http.post<Content>('/api/v1/diary/today', { entry_date: localDate }));
  }

  async list(): Promise<ContentListItem[]> {
    return firstValueFrom(this.http.get<ContentListItem[]>('/api/v1/diary/entries'));
  }
}
