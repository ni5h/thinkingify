export type GrammarFlagStatus = 'pending' | 'self_corrected' | 'kept_as_is';

export interface ExamplePair {
  incorrect: string;
  correct: string;
}

export interface GrammarFlag {
  id: string;
  content_id: string;
  concept_id: string;
  sentence: string;
  status: GrammarFlagStatus;
  attempt_count: number;
  created_at: string;
  concept_label: string;
  concept_rule: string;
  example_pairs: ExamplePair[];
}
