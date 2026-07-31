export interface StageBreakdown {
  found: number;
  self_corrected: number;
  ai_assisted: number;
  kept_as_is: number;
  concepts: string[];
}

export interface ParentReport {
  id: string;
  content_id: string;
  content_title: string;
  style: string | null;
  word_count: number;
  headline: string;
  creativity_narrative: string;
  suggested_action: string | null;
  went_well: string[];
  was_tricky: string[];
  stage_breakdown: {
    spelling: StageBreakdown;
    grammar: StageBreakdown;
    sentence_framing: StageBreakdown;
  };
  ai_help_level: string;
  created_at: string;
}
