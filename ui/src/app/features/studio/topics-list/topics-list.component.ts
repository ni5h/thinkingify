import { Component, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { TopicService } from '../../../core/services/topic.service';
import { AuthService } from '../../../core/services/auth.service';
import { TopicListItem } from '../../../core/models/topic';

@Component({
  selector: 'app-topics-list',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    <div class="flex items-baseline justify-between gap-4">
      <h1 class="font-display text-3xl">Rowling Topics</h1>
      <a routerLink="/studio/topics/new" class="rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors">
        New topic
      </a>
    </div>

    @if ((topics() ?? []).length === 0) {
      <p class="text-muted mt-6">No topics yet.</p>
    } @else {
      <ul class="mt-8 flex flex-col gap-4">
        @for (topic of topics(); track topic.id) {
          <li class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
            <div class="flex items-start justify-between gap-4">
              <div>
                <h2 class="font-display text-xl text-ink">{{ topic.title }}</h2>
                <p class="text-xs text-muted font-mono mt-2">
                  {{ topic.status === 'published' ? 'Published' : 'Draft' }} &middot; updated {{ topic.updated_at | date: 'mediumDate' }}
                </p>
              </div>
            </div>

            @if (isOwner(topic)) {
              <div class="flex flex-wrap gap-2 mt-4">
                <a [routerLink]="['/studio/topics', topic.id, 'edit']" class="rounded-lg bg-cloud px-3 py-1.5 text-sm font-medium text-ink hover:bg-cloud/80 transition-colors">
                  Edit
                </a>
                @if (topic.status === 'draft') {
                  <button
                    type="button"
                    (click)="publish(topic.id)"
                    [disabled]="!topic.audio_url"
                    class="rounded-lg bg-moss/10 px-3 py-1.5 text-sm font-medium text-moss-dark hover:bg-moss/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Publish
                  </button>
                  @if (!topic.audio_url) {
                    <span class="text-xs text-muted self-center">needs audio</span>
                  }
                } @else {
                  <a [routerLink]="['/rowling/topics', topic.slug]" class="rounded-lg px-3 py-1.5 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
                    View live
                  </a>
                  <button type="button" (click)="unpublish(topic.id)" class="rounded-lg bg-amber/10 px-3 py-1.5 text-sm font-medium text-amber hover:bg-amber/20 transition-colors">
                    Unpublish
                  </button>
                }
              </div>
            } @else if (topic.status === 'published') {
              <div class="flex flex-wrap gap-2 mt-4">
                <a [routerLink]="['/rowling/topics', topic.slug]" class="rounded-lg px-3 py-1.5 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
                  View live
                </a>
              </div>
            }
          </li>
        }
      </ul>
    }
  `,
})
export default class TopicsListComponent {
  private readonly topicService = inject(TopicService);
  private readonly auth = inject(AuthService);

  readonly topics = this.topicService.all;

  isOwner(topic: TopicListItem): boolean {
    return topic.author_id === this.auth.currentUser()?.id;
  }

  publish(id: string): void {
    void this.topicService.publish(id);
  }

  unpublish(id: string): void {
    void this.topicService.unpublish(id);
  }
}
