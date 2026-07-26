export interface Puzzle {
  id: string;
  type: 'number-pattern' | 'logic' | 'olympiad' | 'visual';
  title: string;
  prompt: string;
  hint?: string;
  answer: string;
  explanation: string;
  difficulty: 1 | 2 | 3;
}

export interface Lesson {
  id: string;
  title: string;
  subject: 'math' | 'science' | 'philosophy' | 'language' | 'history';
  fact: string;
  deeperThought: string;
  videoUrl?: string;
  pausePrompt: string;
  source?: string;
}

export interface ProgressStats {
  articlesWritten: number;
  puzzlesSolvedCount: number;
  lessonsCompletedCount: number;
  currentStreak: number;
  longestStreak: number;
  totalDaysLearned: number;
  lastActiveDate: string | null;
}

/**
 * Root persisted shape, stored under a single localStorage key.
 * Only raw facts are persisted — counts and streaks are derived in
 * ProgressService via computed(), never stored directly.
 *
 * Blog/Studio content is NOT part of this state — it lives in the backend
 * (Postgres via the FastAPI API) as of Thinkingify Studio v0.1. See
 * core/services/blog.service.ts and core/models/content.ts.
 */
export interface AppState {
  version: number;
  solvedPuzzleIds: string[];
  completedLessonIds: string[];
  /** Distinct YYYY-MM-DD entries, one per day with any qualifying activity. */
  activityDates: string[];
}

// Bumped 3 -> 4 for the removal of `profile` (retired — personalization now
// comes from the real account profile via UserProfileService, not a local
// {name, tagline} pair; see features/profile/profile.component.ts). Only
// additive fields need a StorageService.migrate() backfill; removing a
// field does not — a stale `profile` key in existing users' localStorage is
// simply ignored going forward.
export const APP_STATE_VERSION = 4;

export function createEmptyAppState(): AppState {
  return {
    version: APP_STATE_VERSION,
    solvedPuzzleIds: [],
    completedLessonIds: [],
    activityDates: [],
  };
}
