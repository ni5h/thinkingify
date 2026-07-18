import { Injectable, inject } from '@angular/core';
import { HttpClient, httpResource } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { Topic, TopicDraft, TopicListItem } from '../models/topic';
import { AuthService } from './auth.service';

/**
 * Mirrors BlogService's shape (httpResource() for reads, async writes that
 * .reload() on success) — see ui/CLAUDE.md's Rooms IA section.
 */
@Injectable({ providedIn: 'root' })
export class TopicService {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);

  readonly publishedResource = httpResource<TopicListItem[]>(() => '/api/v1/topics/published');
  readonly allResource = httpResource<TopicListItem[]>(() =>
    this.auth.currentUser()?.role === 'admin' ? '/api/v1/topics' : undefined
  );

  readonly published = this.publishedResource.value;
  readonly all = this.allResource.value;

  async getPublishedBySlug(slug: string): Promise<Topic | undefined> {
    try {
      return await firstValueFrom(this.http.get<Topic>(`/api/v1/topics/published/${slug}`));
    } catch {
      return undefined;
    }
  }

  async getById(id: string): Promise<Topic | undefined> {
    try {
      return await firstValueFrom(this.http.get<Topic>(`/api/v1/topics/${id}`));
    } catch {
      return undefined;
    }
  }

  async create(draft: TopicDraft): Promise<Topic> {
    const topic = await firstValueFrom(this.http.post<Topic>('/api/v1/topics', draft));
    this.reloadAll();
    return topic;
  }

  async update(id: string, changes: Partial<TopicDraft>): Promise<void> {
    await firstValueFrom(this.http.patch<Topic>(`/api/v1/topics/${id}`, changes));
    this.reloadAll();
  }

  async publish(id: string): Promise<void> {
    await this.transition(id, 'publish');
  }

  async unpublish(id: string): Promise<void> {
    await this.transition(id, 'unpublish');
  }

  async delete(id: string): Promise<void> {
    await firstValueFrom(this.http.delete<void>(`/api/v1/topics/${id}`));
    this.reloadAll();
  }

  private async transition(id: string, action: string): Promise<void> {
    await firstValueFrom(this.http.post<Topic>(`/api/v1/topics/${id}/${action}`, {}));
    this.reloadAll();
  }

  private reloadAll(): void {
    this.allResource.reload();
    this.publishedResource.reload();
  }
}
