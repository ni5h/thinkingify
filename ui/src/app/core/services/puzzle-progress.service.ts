import { Injectable, inject } from '@angular/core';
import { HttpClient, httpResource } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { AttemptCreate, AttemptResult, GameProgress, GameStats, TierStats } from '../models/puzzle';
import { AuthService } from './auth.service';

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
  private readonly auth = inject(AuthService);

  // Reused by all 3 metric surfaces (Dashboard sums across games, the
  // Sherlock room shows one row per game, a Kakooma variation page filters
  // to its own game_id) — see ui/CLAUDE.md's Rooms IA section. Gated on
  // auth state since /dashboard itself has no route guard.
  readonly statsResource = httpResource<GameStats[]>(() =>
    this.auth.isAuthenticated() ? '/api/v1/puzzles/stats' : undefined
  );
  readonly stats = this.statsResource.value;

  progressResource(gameId: string) {
    return httpResource<GameProgress>(() => `/api/v1/puzzles/${gameId}/progress`);
  }

  tierStatsResource(gameId: string) {
    return httpResource<TierStats[]>(() => `/api/v1/puzzles/${gameId}/tier-stats`);
  }

  async recordAttempt(gameId: string, attempt: AttemptCreate): Promise<AttemptResult> {
    const result = await firstValueFrom(
      this.http.post<AttemptResult>(`/api/v1/puzzles/${gameId}/attempts`, attempt)
    );
    this.statsResource.reload();
    return result;
  }
}
