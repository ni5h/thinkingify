export type TopicStatus = 'draft' | 'published';

export interface TopicListItem {
  id: string;
  title: string;
  slug: string;
  status: TopicStatus;
  order_index: number;
  updated_at: string;
}

export interface Topic extends TopicListItem {
  explainer_markdown: string;
  audio_url: string | null;
  author_id: string;
  published_at: string | null;
  created_at: string;
}

export interface TopicDraft {
  title: string;
  explainer_markdown?: string;
  audio_url?: string;
  order_index?: number;
}
