import { Component, computed, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { TopicService } from '../../../core/services/topic.service';
import { BlogService } from '../../../core/services/blog.service';
import { TOPIC_THEME_LABELS } from '../../../core/models/theme';

@Component({
  selector: 'app-theme-topics',
  standalone: true,
  imports: [RouterLink, IconComponent],
  template: `
    <a routerLink="/rowling" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
      &larr; Back to Rowling
    </a>

    <h1 class="font-display text-3xl mt-4">{{ label }}</h1>

    @if (topics().length === 0) {
      <p class="text-muted mt-6">No topics for this theme yet.</p>
    } @else {
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6">
        @for (topic of topics(); track topic.id) {
          <a
            [routerLink]="['/rowling/topics', topic.slug]"
            class="rounded-2xl border border-cloud bg-white shadow-sm p-5 hover:shadow-md transition-shadow flex flex-col gap-3"
          >
            <div class="flex items-center gap-3">
              <app-icon name="rowling" [size]="22" class="text-moss shrink-0" />
              <h3 class="font-display text-lg text-ink">{{ topic.title }}</h3>
            </div>
            @if (topic.explainer_markdown) {
              <p class="text-sm text-muted line-clamp-2">{{ topic.explainer_markdown }}</p>
            }
            @if (progressByTopicId().get(topic.id); as p) {
              <span class="text-xs font-mono text-moss-dark bg-moss/10 rounded-full px-2.5 py-1 self-start">
                {{ p === 'published' ? 'Published' : 'In progress' }}
              </span>
            }
          </a>
        }
      </div>
    }
  `,
})
export default class ThemeTopicsComponent {
  private readonly topicService = inject(TopicService);
  private readonly blog = inject(BlogService);
  private readonly route = inject(ActivatedRoute);

  readonly slug = this.route.snapshot.paramMap.get('slug') ?? '';
  readonly label = TOPIC_THEME_LABELS[this.slug] ?? this.slug;

  readonly topics = computed(() =>
    (this.topicService.published() ?? []).filter((t) => t.themes.includes(this.slug))
  );

  readonly progressByTopicId = computed(() => {
    const map = new Map<string, 'draft' | 'published'>();
    for (const post of this.blog.all() ?? []) {
      if (!post.topic_id) continue;
      if (post.status === 'published') map.set(post.topic_id, 'published');
      else if (post.status === 'draft' && !map.has(post.topic_id)) map.set(post.topic_id, 'draft');
    }
    return map;
  });
}
