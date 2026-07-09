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

export interface JournalEntry {
  id: string;
  date: string; // ISO date string YYYY-MM-DD
  title: string;
  whatILearned: string;
  whyIThinkItsTrue: string;
  myOwnExample: string;
  questionsIHave: string;
  whatIllTryTomorrow: string;
  linkedLessonId?: string;
}

export interface Profile {
  name: string; // '' = unset
  tagline: string; // '' = unset, e.g. "one curious eight-year-old"
}

export interface ProgressStats {
  articlesWritten: number;
  puzzlesSolvedCount: number;
  lessonsCompletedCount: number;
  questionsAsked: number;
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
  journalEntries: JournalEntry[];
  solvedPuzzleIds: string[];
  completedLessonIds: string[];
  /** Distinct YYYY-MM-DD entries, one per day with any qualifying activity. */
  activityDates: string[];
  profile: Profile;
}

// Bumped 1 -> 2 for the new `profile` field. StorageService.migrate() only
// backfills createEmptyAppState() defaults when the stored version is
// strictly less than this constant — without the bump, existing saved
// state at version 1 would load with `profile: undefined` and crash.
export const APP_STATE_VERSION = 2;

export function createEmptyAppState(): AppState {
  return {
    version: APP_STATE_VERSION,
    journalEntries: [],
    solvedPuzzleIds: [],
    completedLessonIds: [],
    activityDates: [],
    profile: { name: '', tagline: '' },
  };
}
