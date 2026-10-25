export type CurriculumStatus = 'draft' | 'reviewed' | 'live' | 'retired';
export type AssetKind = 'audio' | 'script' | 'visual';
export type ItemKind = 'recall' | 'apply' | 'explain' | 'spot_the_mistake' | 'puzzle';

export interface Subject {
  id: string;
  name: string;
  code: string;
  grade: number;
}

export interface Chapter {
  id: string;
  subject_id: string;
  title: string;
  order_index: number;
  book_refs: string[];
}

export interface Concept {
  id: string;
  chapter_id: string;
  title: string;
  order_index: number;
  prerequisites: string[];
}

export interface Skill {
  id: string;
  subject_id: string;
  name: string;
  level: number;
}

export interface Item {
  id: string;
  concept_id: string;
  skill_id: string | null;
  kind: ItemKind;
  difficulty: number;
  body: string;
  answer_key: string | null;
  status: CurriculumStatus;
  updated_at: string;
}

// Write shapes (optional fields = PATCH-friendly).
export interface SubjectDraft {
  name: string;
  code: string;
  grade?: number;
}
export interface ChapterDraft {
  subject_id?: string;
  title?: string;
  order_index?: number;
  book_refs?: string[];
}
export interface ConceptDraft {
  chapter_id?: string;
  title?: string;
  order_index?: number;
  prerequisites?: string[];
}
export interface SkillDraft {
  subject_id?: string;
  name?: string;
  level?: number;
}
export interface ItemDraft {
  concept_id?: string;
  skill_id?: string | null;
  kind?: ItemKind;
  difficulty?: number;
  body?: string;
  answer_key?: string | null;
}

export const ITEM_KINDS: ItemKind[] = ['recall', 'apply', 'explain', 'spot_the_mistake', 'puzzle'];
export const CURRICULUM_STATUSES: CurriculumStatus[] = ['draft', 'reviewed', 'live', 'retired'];

export const ITEM_KIND_LABELS: Record<ItemKind, string> = {
  recall: 'Recall',
  apply: 'Apply',
  explain: 'Explain',
  spot_the_mistake: 'Spot the mistake',
  puzzle: 'Puzzle',
};

export const STATUS_LABELS: Record<CurriculumStatus, string> = {
  draft: 'Draft',
  reviewed: 'Reviewed',
  live: 'Live',
  retired: 'Retired',
};

export type StatusCounts = Record<CurriculumStatus, number>;

export interface ConceptContent {
  concept_id: string;
  title: string;
  order_index: number;
  items: StatusCounts;
  assets: StatusCounts;
}

export interface ChapterContent {
  concepts: ConceptContent[];
  item_totals: StatusCounts;
  asset_totals: StatusCounts;
  publishable_count: number;
  live_count: number;
}

export interface PublishResult {
  items: number;
  assets: number;
}
