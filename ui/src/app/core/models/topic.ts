export type TopicStatus = 'draft' | 'published';

export interface TopicListItem {
  id: string;
  title: string;
  slug: string;
  explainer_markdown: string;
  audio_url: string | null;
  status: TopicStatus;
  order_index: number;
  author_id: string;
  updated_at: string;
}

export interface Topic extends TopicListItem {
  published_at: string | null;
  created_at: string;
}

export interface TopicDraft {
  title: string;
  explainer_markdown?: string;
  audio_url?: string;
  order_index?: number;
}
