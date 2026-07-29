export type CompanionMessageRole = 'user' | 'assistant';

export interface CompanionMessage {
  id: string;
  content_id: string;
  role: CompanionMessageRole;
  body: string;
  ladder_level: number | null;
  direct_answer_requested: boolean;
  fact_leak_blocked: boolean;
  is_fallback: boolean;
  created_at: string;
}
