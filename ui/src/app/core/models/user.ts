export type AccountType = 'parent' | 'child';

export interface UserPublicSummary {
  id: string;
  display_name: string | null;
  avatar_url: string | null;
}

export interface UserLinkedProfile {
  id: string;
  email: string;
  avatar_url: string | null;
  account_type: AccountType | null;
  first_name: string | null;
  last_name: string | null;
  username: string | null;
  tagline: string | null;
  school_name: string | null;
  occupation: string | null;
  location_city: string | null;
  location_state: string | null;
  location_country: string | null;
}

export interface UserProfile extends UserLinkedProfile {
  name: string;
  role: 'admin' | 'author' | 'learner';
  is_active: boolean;
  created_at: string;
  profile_completion_percent: number;
}

export interface ProfileUpdate {
  account_type?: AccountType;
  first_name?: string;
  last_name?: string;
  username?: string;
  avatar_url?: string;
  tagline?: string;
  school_name?: string;
  occupation?: string;
  location_city?: string;
  location_state?: string;
  location_country?: string;
}
