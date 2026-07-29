import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { SpellingFlag } from '../models/spelling';

/**
 * Imperative gate logic, not a passive httpResource() read — same shape as
 * CompanionService. The panel component owns the pending-flags list and
 * its attempt/override lifecycle directly.
 */
@Injectable({ providedIn: 'root' })
export class SpellingService {
  private readonly http = inject(HttpClient);

  async list(contentId: string): Promise<SpellingFlag[]> {
    return firstValueFrom(this.http.get<SpellingFlag[]>(`/api/v1/content/${contentId}/spelling/flags`));
  }

  async check(contentId: string, text: string): Promise<SpellingFlag[]> {
    return firstValueFrom(
      this.http.post<SpellingFlag[]>(`/api/v1/content/${contentId}/spelling/check`, { text })
    );
  }

  async attemptFix(contentId: string, flagId: string, word: string): Promise<SpellingFlag> {
    return firstValueFrom(
      this.http.post<SpellingFlag>(`/api/v1/content/${contentId}/spelling/flags/${flagId}/attempt`, { word })
    );
  }

  async override(contentId: string, flagId: string): Promise<SpellingFlag> {
    return firstValueFrom(
      this.http.post<SpellingFlag>(`/api/v1/content/${contentId}/spelling/flags/${flagId}/override`, {})
    );
  }
}
