import { Injectable, inject } from '@angular/core';
import { HttpClient, httpResource } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { AuthService } from './auth.service';
import { BrotherAnswerResult, BrotherSession, BrotherTierState } from '../models/brother';

/**
 * Tier state via httpResource (mirrors PuzzleProgressService/MathService
 * reads); session start + answer as async POSTs (the drill component owns
 * that lifecycle). Correctness is checked server-side — the client never
 * receives an answer before it submits.
 */
@Injectable({ providedIn: 'root' })
export class BrotherService {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);

  readonly stateResource = httpResource<BrotherTierState[]>(() =>
    this.auth.isAuthenticated() ? '/api/v1/brothers/state' : undefined
  );
  readonly state = this.stateResource.value;

  async startSession(): Promise<BrotherSession> {
    return firstValueFrom(this.http.post<BrotherSession>('/api/v1/brothers/sessions', {}));
  }

  async answer(
    sessionId: string,
    index: number,
    userAnswer: number,
    responseMs: number
  ): Promise<BrotherAnswerResult> {
    return firstValueFrom(
      this.http.post<BrotherAnswerResult>(`/api/v1/brothers/sessions/${sessionId}/answers`, {
        index,
        user_answer: userAnswer,
        response_ms: responseMs,
      })
    );
  }

  reloadState(): void {
    this.stateResource.reload();
  }
}
