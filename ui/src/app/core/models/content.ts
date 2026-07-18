export type ContentStatus = 'draft' | 'pending_review' | 'published' | 'archived';
export type WritingStyle = 'documentary' | 'story' | 'fun_casual';

export interface ContentListItem {
  id: string;
  title: string;
  slug: string;
  summary: string | null;
  feature_image_url: string | null;
  status: ContentStatus;
  topic_id: string | null;
  style: WritingStyle | null;
  published_at: string | null;
  updated_at: string;
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
