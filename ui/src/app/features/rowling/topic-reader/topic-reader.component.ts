import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { marked } from 'marked';
import { TopicService } from '../../../core/services/topic.service';
import { NoteService } from '../../../core/services/note.service';
import { Topic } from '../../../core/models/topic';
import { AudioPlayerComponent } from '../../../shared/components/audio-player/audio-player.component';
import { NotesPanelComponent } from '../../../shared/components/notes-panel/notes-panel.component';

@Component({
  selector: 'app-topic-reader',
  standalone: true,
  imports: [RouterLink, AudioPlayerComponent, NotesPanelComponent],
  template: `
    <a routerLink="/rowling" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
      &larr; Back to Rowling
    </a>

    @if (topic()) {
      <div class="md:flex md:gap-6 mt-6">
        <article class="md:flex-1 min-w-0">
          <h1 class="font-display text-3xl text-ink">{{ topic()!.title }}</h1>

          @if (topic()!.audio_url) {
            <div class="mt-4">
              <app-audio-player [src]="topic()!.audio_url!" />
            </div>
          }

          <div class="markdown-content mt-6" [innerHTML]="renderedContent()"></div>

          <div class="mt-10 rounded-2xl border border-cloud bg-white shadow-sm p-6 text-center">
            <p class="font-display text-xl">Ready to write your own take?</p>
            <a
              [routerLink]="['/rowling/topics', slug, 'style']"
              class="inline-block mt-4 rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors"
            >
              Start writing
            </a>
          </div>
        </article>

        <aside class="md:w-80 shrink-0 mt-8 md:mt-0">
          <app-notes-panel
            [body]="noteBody()"
            [status]="autosaveStatus()"
            (bodyChange)="noteBody.set($event)"
            (blurred)="saveNote()"
          />
        </aside>
      </div>
    } @else if (topic() === null) {
      <p class="text-muted mt-6">This topic couldn't be found.</p>
    }
  `,
})
export default class TopicReaderComponent implements OnInit {
  private readonly topicService = inject(TopicService);
  private readonly noteService = inject(NoteService);
  private readonly route = inject(ActivatedRoute);

  readonly slug = this.route.snapshot.paramMap.get('slug') ?? '';
  readonly topic = signal<Topic | null | undefined>(undefined);

  readonly noteBody = signal('');
  readonly autosaveStatus = signal<string | null>(null);

  readonly renderedContent = computed(() => {
    const topic = this.topic();
    return topic ? marked.parse(topic.explainer_markdown, { async: false }) : '';
  });

  async ngOnInit(): Promise<void> {
    const topic = await this.topicService.getPublishedBySlug(this.slug);
    this.topic.set(topic ?? null);
    if (!topic) return;

    const note = await this.noteService.getOrCreate(topic.id);
    this.noteBody.set(note.body);
  }

  async saveNote(): Promise<void> {
    const topic = this.topic();
    if (!topic) return;
    await this.noteService.update(topic.id, this.noteBody());
    this.autosaveStatus.set(`Saved ${new Date().toLocaleTimeString()}`);
  }
}
