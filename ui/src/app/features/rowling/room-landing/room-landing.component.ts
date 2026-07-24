import { Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { TopicService } from '../../../core/services/topic.service';
import { BlogService } from '../../../core/services/blog.service';
import { TOPIC_THEMES } from '../../../core/models/theme';

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
          words. Pick a theme below to find a topic, take some notes as you go, then write your
          own take &mdash; documentary, story, or just for fun. Or skip straight to a blank page
          with "Write your own."
        </p>
      </div>
    </div>

    <h2 class="font-display text-xl mt-10">Get started</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
      <a
        routerLink="/studio/posts/new"
        class="rounded-2xl border border-amber/40 bg-amber/5 shadow-sm p-5 hover:shadow-md transition-shadow flex items-center justify-between gap-3"
      >
        <div>
          <h3 class="font-display text-lg text-ink">Write your own</h3>
          <p class="text-sm text-muted mt-1">No topic, no rules &mdash; just write.</p>
        </div>
        <app-icon name="arrow-right" [size]="20" class="text-amber shrink-0" />
      </a>
      @for (theme of themeCards(); track theme.slug) {
        <a
          [routerLink]="['/rowling/themes', theme.slug]"
          class="rounded-2xl border border-cloud bg-white shadow-sm p-5 hover:shadow-md transition-shadow flex flex-col gap-1"
        >
          <h3 class="font-display text-lg text-ink">{{ theme.label }}</h3>
          <p class="text-sm text-muted">{{ theme.count }} topic{{ theme.count === 1 ? '' : 's' }}</p>
        </a>
      }
    </div>

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

  readonly themeCards = computed(() => {
    const counts = new Map<string, number>();
    for (const topic of this.topicService.published() ?? []) {
      for (const slug of topic.themes) counts.set(slug, (counts.get(slug) ?? 0) + 1);
    }
    // Curated catalog order; only themes with >=1 published topic, so a
    // theme card never leads to a dead-end empty listing.
    return TOPIC_THEMES.filter((t) => counts.has(t.slug)).map((t) => ({ ...t, count: counts.get(t.slug)! }));
  });

  // Not filtered to .topic_id-having posts — BlogService.all() is already
  // scoped to the current user server-side, so this safely includes
  // "Write your own" freeform posts (no topic_id) alongside topic-linked ones.
  private readonly ownPosts = computed(() => this.blog.all() ?? []);
  readonly drafts = computed(() => this.ownPosts().filter((p) => p.status === 'draft'));
  readonly published = computed(() => this.ownPosts().filter((p) => p.status === 'published'));
}
