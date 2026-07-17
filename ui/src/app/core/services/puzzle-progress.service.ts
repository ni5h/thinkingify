import { Injectable, inject } from '@angular/core';
import { HttpClient, httpResource } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { AttemptCreate, AttemptResult, GameProgress } from '../models/puzzle';

/**
 * Progress is single-writer (only this learner, only this component, ever
 * mutates their own row), and recordAttempt()'s response already contains
 * the fresh GameProgress, so callers update local state straight from the
 * response instead of re-fetching — a deliberate deviation from
 * BlogService's "always .reload() after a write" convention, not an
 * oversight, since there's no concurrent-modification concern here to
 * guard against.
 */
@Injectable({ providedIn: 'root' })
export class PuzzleProgressService {
  private readonly http = inject(HttpClient);

  progressResource(gameId: string) {
    return httpResource<GameProgress>(() => `/api/v1/puzzles/${gameId}/progress`);
  }

  async recordAttempt(gameId: string, attempt: AttemptCreate): Promise<AttemptResult> {
    return firstValueFrom(this.http.post<AttemptResult>(`/api/v1/puzzles/${gameId}/attempts`, attempt));
  }
}
