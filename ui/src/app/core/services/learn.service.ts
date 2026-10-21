import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

// Learner-facing concept-map reads + the server-driven quick-check session.
// Grading, the staircase level and mastery all live on the server — this
// service never sees a level or a score.

export interface LearnSubject {
  id: string;
  name: string;
  code: string;
  grade: number;
}

export interface LearnChapter {
  id: string;
  subject_id: string;
  title: string;
  order_index: number;
}

export interface LearnConcept {
  id: string;
  chapter_id: string;
  title: string;
  order_index: number;
  prerequisites: string[];
}

export type ConceptState = 'learning' | 'solid' | 'needs_look';

export interface ConceptProgress {
  concept_id: string;
  state: ConceptState;
  available: boolean;
  mastered: boolean;
}

export interface CardThink {
  q: string;
  options: string[];
  answer_index: number;
  why: string;
}

export interface CardData {
  title: string;
  text: string;
  visual_brief: string;
  visual_svg?: string | null;
  audio_script: string;
  think: CardThink;
}

export interface RecapData {
  lines: string[];
  remember: string;
}

export interface LearnAsset {
  id: string;
  concept_id: string;
  kind: 'audio' | 'script' | 'visual' | 'card' | 'recap';
  url: string | null;
  order_index: number;
  data: CardData | RecapData | null;
}

export interface CheckItem {
  id: string;
  concept_id: string;
  kind: string;
  body: string;
  options: string[] | null;
}

export interface CheckSession {
  session_id: string;
  index: number;
  total: number;
  item: CheckItem | null;
  done: boolean;
}

export interface AnswerResult {
  correct: boolean;
  unsure: boolean;
  reveal_answer: string | null;
  hint: string | null;
  source_asset_id: string | null;
  index: number;
  total: number;
  done: boolean;
  next_item: CheckItem | null;
  skip_earned?: boolean | null;
}

@Injectable({ providedIn: 'root' })
export class LearnService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/curriculum';

  getSubjects(): Promise<LearnSubject[]> {
    return firstValueFrom(this.http.get<LearnSubject[]>(`${this.base}/subjects`));
  }
  getChapters(subjectId: string): Promise<LearnChapter[]> {
    return firstValueFrom(this.http.get<LearnChapter[]>(`${this.base}/subjects/${subjectId}/chapters`));
  }
  getConcepts(chapterId: string): Promise<LearnConcept[]> {
    return firstValueFrom(this.http.get<LearnConcept[]>(`${this.base}/chapters/${chapterId}/concepts`));
  }
  getProgress(chapterId: string): Promise<ConceptProgress[]> {
    return firstValueFrom(this.http.get<ConceptProgress[]>(`${this.base}/chapters/${chapterId}/progress`));
  }
  getAssets(conceptId: string): Promise<LearnAsset[]> {
    return firstValueFrom(this.http.get<LearnAsset[]>(`${this.base}/concepts/${conceptId}/assets`));
  }

  startCheck(conceptId: string, thinkResults: string[], mode: 'check' | 'challenge' = 'check'): Promise<CheckSession> {
    return firstValueFrom(
      this.http.post<CheckSession>(`${this.base}/concepts/${conceptId}/check/start`, {
        think_results: thinkResults,
        mode,
      }),
    );
  }

  answer(
    sessionId: string,
    body: { item_id: string; choice?: string | null; unsure?: boolean; hint_used?: boolean; ms?: number | null },
  ): Promise<AnswerResult> {
    return firstValueFrom(this.http.post<AnswerResult>(`${this.base}/check/${sessionId}/answer`, body));
  }
}
