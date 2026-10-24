import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

export interface ChildRef {
  id: string;
  name: string;
}

export type ConceptStateValue = 'learning' | 'solid' | 'needs_look';
export type WorkingAt = 'comfortable' | 'stretching' | null;

export interface ConceptState {
  concept_id: string;
  title: string;
  state: ConceptStateValue;
  working_at: WorkingAt;
}

export interface ChapterState {
  chapter_id: string;
  subject: string;
  title: string;
  concepts: ConceptState[];
}

export interface RecentActivity {
  concept_title: string;
  when: string;
}

export interface ParentOverview {
  child: ChildRef;
  time_this_week_minutes: number;
  solid_count: number;
  total_concepts: number;
  chapters: ChapterState[];
  recent: RecentActivity[];
}

export interface ParentDigest {
  lines: string[];
}

@Injectable({ providedIn: 'root' })
export class ParentService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1';

  getChildren(): Promise<ChildRef[]> {
    return firstValueFrom(this.http.get<ChildRef[]>(`${this.base}/parent/children`));
  }
  getOverview(childId: string): Promise<ParentOverview> {
    return firstValueFrom(this.http.get<ParentOverview>(`${this.base}/parent/children/${childId}/overview`));
  }
  getDigest(childId: string): Promise<ParentDigest> {
    return firstValueFrom(this.http.get<ParentDigest>(`${this.base}/parent/children/${childId}/digest`));
  }

  /** Learner reports active seconds on a concept. Fire-and-forget. */
  reportActivity(body: { concept_id?: string | null; context?: string; seconds: number }): void {
    this.http.post(`${this.base}/me/activity`, body).subscribe({ error: () => {} });
  }
}
