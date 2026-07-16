import { Injectable, inject } from '@angular/core';
import { HttpClient, httpResource } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { Content, ContentDraft, ContentListItem } from '../models/content';
import { AuthService } from './auth.service';

/**
 * API-backed replacement for the old localStorage BlogService. Reads use
 * httpResource() (signals, no manual subscription management, consistent
 * with the project's "no RxJS for app state" rule); writes are plain async
 * methods that .reload() the relevant resource on success — the one real
 * architectural loss vs. localStorage, where every read auto-derived from
 * one signal. See ui/CLAUDE.md and api/app/services/content_service.py.
 */
@Injectable({ providedIn: 'root' })
export class BlogService {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);

  readonly publishedResource = httpResource<ContentListItem[]>(() => '/api/v1/content/published');
  // Gated on auth state: `allResource` is a class-field initializer, so it
  // starts fetching the moment BlogService is injected anywhere — including
  // public, unauthenticated pages (/dashboard, /blog, /blog/:slug). Returning
  // undefined tells httpResource not to fetch; it re-evaluates reactively, so
  // this starts fetching once the user actually signs in.
  readonly allResource = httpResource<ContentListItem[]>(() =>
    this.auth.isAuthenticated() ? '/api/v1/content' : undefined
  );

  readonly published = this.publishedResource.value;
  readonly all = this.allResource.value;

  async getPublishedBySlug(slug: string): Promise<Content | undefined> {
    try {
      return await firstValueFrom(this.http.get<Content>(`/api/v1/content/published/${slug}`));
    } catch {
      return undefined;
    }
  }

  async getById(id: string): Promise<Content | undefined> {
    try {
      return await firstValueFrom(this.http.get<Content>(`/api/v1/content/${id}`));
    } catch {
      return undefined;
    }
  }

  async create(draft: ContentDraft): Promise<Content> {
    const post = await firstValueFrom(this.http.post<Content>('/api/v1/content', draft));
    this.reloadAll();
    return post;
  }

  async update(id: string, changes: Partial<ContentDraft>): Promise<void> {
    await firstValueFrom(this.http.patch<Content>(`/api/v1/content/${id}`, changes));
    this.reloadAll();
  }

  async submitForReview(id: string): Promise<void> {
    await this.transition(id, 'submit-for-review');
  }

  async backToDraft(id: string): Promise<void> {
    await this.transition(id, 'back-to-draft');
  }

  async publish(id: string): Promise<void> {
    await this.transition(id, 'publish');
  }

  async archive(id: string): Promise<void> {
    await this.transition(id, 'archive');
  }

  async republish(id: string): Promise<void> {
    await this.transition(id, 'republish');
  }

  async delete(id: string): Promise<void> {
    await firstValueFrom(this.http.delete<void>(`/api/v1/content/${id}`));
    this.reloadAll();
  }

  private async transition(id: string, action: string): Promise<void> {
    await firstValueFrom(this.http.post<Content>(`/api/v1/content/${id}/${action}`, {}));
    this.reloadAll();
  }

  private reloadAll(): void {
    this.allResource.reload();
    this.publishedResource.reload();
  }
}
