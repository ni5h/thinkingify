import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { Note } from '../models/note';

/**
 * One evolving scratchpad per topic per learner. Plain async methods, not
 * httpResource() — the topic reader / writing studio own the get-or-create
 * + autosave lifecycle directly (same shape as JournalService's usage).
 */
@Injectable({ providedIn: 'root' })
export class NoteService {
  private readonly http = inject(HttpClient);

  async getOrCreate(topicId: string): Promise<Note> {
    return firstValueFrom(this.http.get<Note>(`/api/v1/topics/${topicId}/notes`));
  }

  async update(topicId: string, body: string): Promise<Note> {
    return firstValueFrom(this.http.patch<Note>(`/api/v1/topics/${topicId}/notes`, { body }));
  }

  // Blank "Write your own" posts have no topic, so their scratchpad is
  // scoped by the content row itself.
  async getOrCreateForContent(contentId: string): Promise<Note> {
    return firstValueFrom(this.http.get<Note>(`/api/v1/content/${contentId}/notes`));
  }

  async updateForContent(contentId: string, body: string): Promise<Note> {
    return firstValueFrom(this.http.patch<Note>(`/api/v1/content/${contentId}/notes`, { body }));
  }
}
