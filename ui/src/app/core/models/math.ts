export type MathCoachMessageRole = 'user' | 'assistant';

export interface MathProblemListItem {
  id: string;
  title: string;
  slug: string;
  concept_tags: string[];
  difficulty: number;
  order_index: number;
}

export interface MathProblemDetail {
  id: string;
  title: string;
  slug: string;
  statement_markdown: string;
  concept_tags: string[];
  difficulty: number;
  status: 'draft' | 'published';
  order_index: number;
}

export interface MathCoachMessage {
  id: string;
  math_problem_id: string;
  role: MathCoachMessageRole;
  body: string;
  ladder_level: number | null;
  asked_for_answer: boolean;
  answer_leak_blocked: boolean;
  is_fallback: boolean;
  created_at: string;
}

export interface MathAttempt {
  id: string;
  math_problem_id: string;
  submitted_answer: string;
  is_correct: boolean;
  created_at: string;
  // Present only on a correct attempt — the post-solve payoff.
  solution_markdown: string | null;
}
