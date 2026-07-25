export type FamilyLinkStatus = 'pending' | 'accepted';
export type TargetRole = 'guardian' | 'child';

export interface UserSummary {
  id: string;
  name: string;
  email: string;
  avatar_url: string | null;
}

export interface FamilyLink {
  id: string;
  status: FamilyLinkStatus;
  requested_by: string;
  guardian: UserSummary;
  child: UserSummary;
  created_at: string;
  accepted_at: string | null;
}

export interface FamilyLinksOut {
  as_guardian: FamilyLink[];
  as_child: FamilyLink[];
}

export interface ChildSummary {
  child_id: string;
  child_name: string;
  total_puzzle_attempts: number;
  puzzle_attempts_this_week: number;
  published_post_count: number;
}
