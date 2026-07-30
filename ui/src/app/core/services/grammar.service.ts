import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { GrammarFlag } from '../models/grammar';

/**
 * Imperative gate logic, not a passive httpResource() read — same shape
 * as SpellingService/CompanionService. The panel component owns the
 * pending-flags list and its attempt/override lifecycle directly.
 */
@Injectable({ providedIn: 'root' })
export class GrammarService {
  private readonly http = inject(HttpClient);

  async list(contentId: string): Promise<GrammarFlag[]> {
    return firstValueFrom(this.http.get<GrammarFlag[]>(`/api/v1/content/${contentId}/grammar/flags`));
  }

  async check(contentId: string, text: string): Promise<GrammarFlag[]> {
    return firstValueFrom(
      this.http.post<GrammarFlag[]>(`/api/v1/content/${contentId}/grammar/check`, { text })
    );
  }

  async attemptFix(contentId: string, flagId: string, sentence: string): Promise<GrammarFlag> {
    return firstValueFrom(
      this.http.post<GrammarFlag>(`/api/v1/content/${contentId}/grammar/flags/${flagId}/attempt`, { sentence })
    );
  }

  async override(contentId: string, flagId: string): Promise<GrammarFlag> {
    return firstValueFrom(
      this.http.post<GrammarFlag>(`/api/v1/content/${contentId}/grammar/flags/${flagId}/override`, {})
    );
  }
}
