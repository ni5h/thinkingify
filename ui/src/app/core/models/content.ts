import { UserPublicSummary } from './user';

export type ContentStatus = 'draft' | 'pending_review' | 'published' | 'archived';
export type WritingStyle = 'fairy_tale' | 'news_report' | 'diary_entry' | 'letter' | 'how_to' | 'blank';

export interface ContentListItem {
  id: string;
  title: string;
  slug: string;
  summary: string | null;
  feature_image_url: string | null;
  status: ContentStatus;
  topic_id: string | null;
  // Deliberately string, not WritingStyle — read path, may hold a value
  // from before the style set last changed. WritingStyle (strict) is only
  // enforced on writes, see ContentDraft below.
  style: string | null;
  published_at: string | null;
  updated_at: string;
  // Only populated on the public /content/published* endpoints.
  author: UserPublicSummary | null;
}

export interface Content extends ContentListItem {
  content_markdown: string;
  author_id: string;
  created_at: string;
}

export interface ContentDraft {
  title: string;
  summary?: string;
  content_markdown?: string;
  feature_image_url?: string;
  topic_id?: string;
  style?: WritingStyle;
}
