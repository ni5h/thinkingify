import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient, httpResource } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import {
  Chapter,
  ChapterDraft,
  Concept,
  ConceptDraft,
  CurriculumStatus,
  Item,
  ItemDraft,
  ItemKind,
  Skill,
  SkillDraft,
  Subject,
  SubjectDraft,
} from '../models/curriculum';
import { AuthService } from './auth.service';

export interface ItemFilter {
  status?: CurriculumStatus;
  concept_id?: string;
  skill_id?: string;
  kind?: ItemKind;
}

/**
 * Admin-only concept-map CRUD. Mirrors TopicService (httpResource reads, async
 * writes that .reload() on success; transitions via POST /:id/{action}).
 * The whole tree is small, so the tree screen reads all chapters/concepts and
 * assembles client-side.
 */
@Injectable({ providedIn: 'root' })
export class CurriculumService {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);
  private readonly base = '/api/v1/admin/curriculum';

  private url(path: string): string | undefined {
    return this.auth.isAuthenticated() ? `${this.base}${path}` : undefined;
  }

  readonly subjectsResource = httpResource<Subject[]>(() => this.url('/subjects'));
  readonly chaptersResource = httpResource<Chapter[]>(() => this.url('/chapters'));
  readonly conceptsResource = httpResource<Concept[]>(() => this.url('/concepts'));
  readonly skillsResource = httpResource<Skill[]>(() => this.url('/skills'));

  readonly subjects = this.subjectsResource.value;
  readonly chapters = this.chaptersResource.value;
  readonly concepts = this.conceptsResource.value;
  readonly skills = this.skillsResource.value;

  // Item list, reactive to a filter signal.
  readonly itemFilter = signal<ItemFilter>({});
  readonly itemsResource = httpResource<Item[]>(() => {
    if (!this.auth.isAuthenticated()) return undefined;
    const f = this.itemFilter();
    const qs = new URLSearchParams();
    if (f.status) qs.set('status_filter', f.status);
    if (f.concept_id) qs.set('concept_id', f.concept_id);
    if (f.skill_id) qs.set('skill_id', f.skill_id);
    if (f.kind) qs.set('kind', f.kind);
    const q = qs.toString();
    return `${this.base}/items${q ? '?' + q : ''}`;
  });
  readonly items = this.itemsResource.value;

  readonly reviewResource = httpResource<Item[]>(() => this.url('/review'));
  readonly reviewItems = this.reviewResource.value;

  readonly conceptsById = computed(
    () => new Map((this.concepts() ?? []).map((c) => [c.id, c])),
  );

  async getItem(id: string): Promise<Item | undefined> {
    try {
      return await firstValueFrom(this.http.get<Item>(`${this.base}/items/${id}`));
    } catch {
      return undefined;
    }
  }

  // --- writes ---
  async createSubject(d: SubjectDraft): Promise<Subject> {
    const s = await firstValueFrom(this.http.post<Subject>(`${this.base}/subjects`, d));
    this.subjectsResource.reload();
    return s;
  }
  async createChapter(d: ChapterDraft): Promise<Chapter> {
    const c = await firstValueFrom(this.http.post<Chapter>(`${this.base}/chapters`, d));
    this.chaptersResource.reload();
    return c;
  }
  async updateChapter(id: string, d: ChapterDraft): Promise<void> {
    await firstValueFrom(this.http.patch(`${this.base}/chapters/${id}`, d));
    this.chaptersResource.reload();
  }
  async createConcept(d: ConceptDraft): Promise<Concept> {
    const c = await firstValueFrom(this.http.post<Concept>(`${this.base}/concepts`, d));
    this.conceptsResource.reload();
    return c;
  }
  async updateConcept(id: string, d: ConceptDraft): Promise<void> {
    await firstValueFrom(this.http.patch(`${this.base}/concepts/${id}`, d));
    this.conceptsResource.reload();
  }
  async createSkill(d: SkillDraft): Promise<Skill> {
    const s = await firstValueFrom(this.http.post<Skill>(`${this.base}/skills`, d));
    this.skillsResource.reload();
    return s;
  }

  async createItem(d: ItemDraft): Promise<Item> {
    const item = await firstValueFrom(this.http.post<Item>(`${this.base}/items`, d));
    this.reloadItems();
    return item;
  }
  async updateItem(id: string, d: ItemDraft): Promise<void> {
    await firstValueFrom(this.http.patch(`${this.base}/items/${id}`, d));
    this.reloadItems();
  }
  async transitionItem(id: string, action: string): Promise<void> {
    await firstValueFrom(this.http.post(`${this.base}/items/${id}/${action}`, {}));
    this.reloadItems();
  }
  async deleteItem(id: string): Promise<void> {
    await firstValueFrom(this.http.delete(`${this.base}/items/${id}`));
    this.reloadItems();
  }

  private reloadItems(): void {
    this.itemsResource.reload();
    this.reviewResource.reload();
  }
}
