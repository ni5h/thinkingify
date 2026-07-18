import { Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { TopicService } from '../../../core/services/topic.service';
import { BlogService } from '../../../core/services/blog.service';

@Component({
  selector: 'app-room-landing',
  standalone: true,
  imports: [RouterLink, IconComponent],
  template: `
    <div class="flex items-start gap-4">
      <app-icon name="rowling" [size]="32" class="text-moss shrink-0 mt-1" />
      <div>
        <h1 class="font-display text-3xl">Rowling</h1>
        <p class="text-muted mt-2 max-w-prose">
          Every great story starts with paying close attention, then telling it back in your own
          words. Pick a topic below, take some notes as you go, then write your own take &mdash;
          documentary, story, or just for fun.
        </p>
      </div>
    </div>

    <h2 class="font-display text-xl mt-10">Topics</h2>
    @if ((topics() ?? []).length === 0) {
      <p class="text-muted mt-4">No topics published yet &mdash; check back soon.</p>
    } @else {
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
        @for (topic of topics(); track topic.id) {
          <a
            [routerLink]="['/rowling/topics', topic.slug]"
            class="rounded-2xl border border-cloud bg-white shadow-sm p-5 hover:shadow-md transition-shadow flex items-center gap-3"
          >
            <app-icon name="rowling" [size]="22" class="text-moss shrink-0" />
            <h3 class="font-display text-lg text-ink">{{ topic.title }}</h3>
          </a>
        }
      </div>
    }

    @if (drafts().length > 0 || published().length > 0) {
      <h2 class="font-display text-xl mt-10">Continue writing</h2>
      <ul class="mt-4 flex flex-col gap-2">
        @for (post of drafts(); track post.id) {
          <li>
            <a [routerLink]="['/rowling/write', post.id]" class="text-ink text-sm font-medium hover:underline">
              {{ post.title || '(untitled)' }}
            </a>
            <span class="text-xs text-muted font-mono ml-2">draft</span>
          </li>
        }
        @for (post of published(); track post.id) {
          <li>
            <a [routerLink]="['/blog', post.slug]" class="text-ink text-sm font-medium hover:underline">{{ post.title }}</a>
            <span class="text-xs text-muted font-mono ml-2">published</span>
          </li>
        }
      </ul>
    }
  `,
})
export default class RoomLandingComponent {
  private readonly topicService = inject(TopicService);
  private readonly blog = inject(BlogService);

  readonly topics = this.topicService.published;

  private readonly ownRowlingPosts = computed(() => (this.blog.all() ?? []).filter((p) => p.topic_id));
  readonly drafts = computed(() => this.ownRowlingPosts().filter((p) => p.status === 'draft'));
  readonly published = computed(() => this.ownRowlingPosts().filter((p) => p.status === 'published'));
}
