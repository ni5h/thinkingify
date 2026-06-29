import { Injectable, computed, inject } from '@angular/core';
import { StorageService } from './storage.service';
import { BlogPost } from '../models';

export type BlogPostDraft = Pick<BlogPost, 'title' | 'tagline' | 'contentMarkdown'> & {
  coverImageDataUrl?: string;
};

@Injectable({ providedIn: 'root' })
export class BlogService {
  private readonly storage = inject(StorageService);

  readonly all = computed(() =>
    [...this.storage.state().blogPosts].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
  );

  readonly published = computed(() =>
    this.all()
      .filter((post) => post.status === 'published')
      .sort((a, b) => (b.publishedAt ?? '').localeCompare(a.publishedAt ?? ''))
  );

  getById(id: string): BlogPost | undefined {
    return this.storage.state().blogPosts.find((post) => post.id === id);
  }

  create(draft: BlogPostDraft): BlogPost {
    const now = new Date().toISOString();
    const post: BlogPost = {
      ...draft,
      id: crypto.randomUUID(),
      status: 'draft',
      createdAt: now,
      updatedAt: now,
    };
    this.storage.update((state) => ({
      ...state,
      blogPosts: [...state.blogPosts, post],
    }));
    return post;
  }

  update(id: string, changes: Partial<BlogPostDraft>): void {
    this.storage.update((state) => ({
      ...state,
      blogPosts: state.blogPosts.map((post) =>
        post.id === id ? { ...post, ...changes, updatedAt: new Date().toISOString() } : post
      ),
    }));
  }

  submitForReview(id: string): void {
    this.setStatus(id, 'pending_review');
  }

  backToDraft(id: string): void {
    this.setStatus(id, 'draft');
  }

  publish(id: string): void {
    const now = new Date().toISOString();
    this.storage.update((state) => ({
      ...state,
      blogPosts: state.blogPosts.map((post) =>
        post.id === id
          ? { ...post, status: 'published', publishedAt: post.publishedAt ?? now, updatedAt: now }
          : post
      ),
    }));
    this.storage.recordActivityToday();
  }

  archive(id: string): void {
    this.setStatus(id, 'archived');
  }

  republish(id: string): void {
    this.setStatus(id, 'published');
  }

  delete(id: string): void {
    this.storage.update((state) => ({
      ...state,
      blogPosts: state.blogPosts.filter((post) => post.id !== id),
    }));
  }

  private setStatus(id: string, status: BlogPost['status']): void {
    this.storage.update((state) => ({
      ...state,
      blogPosts: state.blogPosts.map((post) =>
        post.id === id ? { ...post, status, updatedAt: new Date().toISOString() } : post
      ),
    }));
  }
}
