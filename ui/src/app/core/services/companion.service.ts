import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { CompanionMessage } from '../models/companion';

/**
 * The writing companion's chat thread for a single draft. Plain async
 * methods, not httpResource() — same shape as NoteService, the panel
 * component owns the message-list/loading lifecycle directly.
 */
@Injectable({ providedIn: 'root' })
export class CompanionService {
  private readonly http = inject(HttpClient);

  async list(contentId: string): Promise<CompanionMessage[]> {
    return firstValueFrom(this.http.get<CompanionMessage[]>(`/api/v1/content/${contentId}/companion/messages`));
  }

  async send(contentId: string, body: string, sessionId: string): Promise<CompanionMessage> {
    return firstValueFrom(
      this.http.post<CompanionMessage>(`/api/v1/content/${contentId}/companion/messages`, {
        body,
        session_id: sessionId,
      })
    );
  }
}
