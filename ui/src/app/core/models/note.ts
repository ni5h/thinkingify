export interface Note {
  id: string;
  topic_id: string | null;
  content_id: string | null;
  user_id: string;
  body: string;
  updated_at: string;
}
