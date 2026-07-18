import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink, ActivatedRoute, Router } from '@angular/router';
import { TopicService } from '../../../core/services/topic.service';
import { BlogService } from '../../../core/services/blog.service';
import { Topic } from '../../../core/models/topic';
import { WritingStyle } from '../../../core/models/content';

interface StyleOption {
  value: WritingStyle;
  label: string;
  description: string;
}

const STYLES: StyleOption[] = [
  { value: 'documentary', label: 'Documentary', description: 'Explain it like you’re narrating the facts.' },
  { value: 'story', label: 'Story', description: 'Two friends talking it through.' },
  { value: 'fun_casual', label: 'Fun & casual', description: 'Whatever way feels natural to you.' },
];

@Component({
  selector: 'app-style-chooser',
  standalone: true,
  imports: [RouterLink],
  template: `
    <a [routerLink]="['/rowling/topics', slug]" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
      &larr; Back to topic
    </a>

    @if (topic()) {
      <h1 class="font-display text-3xl mt-6">Pick a style</h1>
      <p class="text-muted mt-2">How do you want to tell it?</p>

      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8">
        @for (style of styles; track style.value) {
          <button
            type="button"
            [disabled]="starting()"
            (click)="start(style.value)"
            class="text-left rounded-2xl border border-cloud bg-white shadow-sm p-5 hover:shadow-md transition-shadow disabled:opacity-60"
          >
            <h2 class="font-display text-lg text-ink">{{ style.label }}</h2>
            <p class="text-muted text-sm mt-1">{{ style.description }}</p>
          </button>
        }
      </div>
    }
  `,
})
export default class StyleChooserComponent implements OnInit {
  private readonly topicService = inject(TopicService);
  private readonly blog = inject(BlogService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly slug = this.route.snapshot.paramMap.get('slug') ?? '';
  readonly topic = signal<Topic | null>(null);
  readonly starting = signal(false);
  readonly styles = STYLES;

  async ngOnInit(): Promise<void> {
    const topic = await this.topicService.getPublishedBySlug(this.slug);
    this.topic.set(topic ?? null);
  }

  async start(style: WritingStyle): Promise<void> {
    const topic = this.topic();
    if (!topic) return;
    this.starting.set(true);
    const post = await this.blog.create({ title: topic.title, topic_id: topic.id, style });
    await this.router.navigate(['/rowling/write', post.id], { replaceUrl: true });
  }
}
