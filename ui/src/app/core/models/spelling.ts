export type SpellingErrorType = 'misspelling' | 'homophone';
export type SpellingFlagStatus = 'pending' | 'self_corrected' | 'kept_as_is';

export interface SpellingFlag {
  id: string;
  content_id: string;
  word: string;
  error_type: SpellingErrorType;
  context_sentence: string;
  suggested_correction: string | null;
  hint: string | null;
  status: SpellingFlagStatus;
  hint_revealed: boolean;
  attempt_count: number;
  created_at: string;
}
