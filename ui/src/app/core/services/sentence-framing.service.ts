import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { SentenceFramingFlag } from '../models/sentence-framing';

/**
 * Imperative gate logic, same shape as GrammarService/SpellingService.
 * `check` takes `sections: string[]` (not a flat `text: string`) — this
 * stage detects runs of consecutive sentences, which must never span a
 * Rowling section boundary, so the caller passes each section's text
 * separately rather than a joined string.
 */
@Injectable({ providedIn: 'root' })
export class SentenceFramingService {
  private readonly http = inject(HttpClient);

  async list(contentId: string): Promise<SentenceFramingFlag[]> {
    return firstValueFrom(
      this.http.get<SentenceFramingFlag[]>(`/api/v1/content/${contentId}/sentence-framing/flags`)
    );
  }

  async check(contentId: string, sections: string[]): Promise<SentenceFramingFlag[]> {
    return firstValueFrom(
      this.http.post<SentenceFramingFlag[]>(`/api/v1/content/${contentId}/sentence-framing/check`, { sections })
    );
  }

  async attemptFix(contentId: string, flagId: string, sentences: string): Promise<SentenceFramingFlag> {
    return firstValueFrom(
      this.http.post<SentenceFramingFlag>(
        `/api/v1/content/${contentId}/sentence-framing/flags/${flagId}/attempt`,
        { sentences }
      )
    );
  }

  async override(contentId: string, flagId: string): Promise<SentenceFramingFlag> {
    return firstValueFrom(
      this.http.post<SentenceFramingFlag>(
        `/api/v1/content/${contentId}/sentence-framing/flags/${flagId}/override`,
        {}
      )
    );
  }
}
