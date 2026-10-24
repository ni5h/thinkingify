import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CurriculumService } from '../../../core/services/curriculum.service';
import { ChapterContent, StatusCounts } from '../../../core/models/curriculum';

@Component({
  selector: 'app-chapter-publish',
  standalone: true,
  imports: [RouterLink],
  template: `
    <a routerLink="/studio/curriculum" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">&larr; Curriculum</a>
    <h1 class="font-display text-3xl mt-4">Review &amp; publish</h1>
    <p class="text-muted mt-1">{{ chapterTitle() }}</p>

    @if (loading()) {
      <p class="text-muted mt-6">Loading…</p>
    } @else if (content(); as c) {
      <!-- Totals -->
      <div class="grid grid-cols-2 gap-4 mt-6">
        <div class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
          <p class="text-xs text-muted font-mono">Waiting to publish</p>
          <p class="font-display text-3xl text-ink mt-1">{{ c.publishable_count }}</p>
          <p class="text-xs text-muted mt-1">cards &amp; questions in draft or reviewed</p>
        </div>
        <div class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
          <p class="text-xs text-muted font-mono">Already live</p>
          <p class="font-display text-3xl text-ink mt-1">{{ c.live_count }}</p>
          <p class="text-xs text-muted mt-1">visible to learners now</p>
        </div>
      </div>

      <!-- Actions -->
      <div class="mt-5 flex flex-wrap items-center gap-3">
        <button type="button"
          class="rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors disabled:opacity-50"
          [disabled]="busy() || c.publishable_count === 0"
          (click)="publish()">
          Publish {{ c.publishable_count }} to live
        </button>
        @if (c.live_count > 0) {
          <button type="button"
            class="rounded-xl bg-amber/10 px-4 py-2.5 text-sm font-medium text-amber hover:bg-amber/20 transition-colors disabled:opacity-50"
            [disabled]="busy()"
            (click)="retire()">
            Unpublish live content
          </button>
        }
        @if (message()) { <span class="text-sm text-moss-dark">{{ message() }}</span> }
      </div>

      <!-- Per-concept breakdown -->
      <h2 class="font-display text-lg mt-8">By concept</h2>
      <div class="mt-3 flex flex-col gap-2">
        @for (con of c.concepts; track con.concept_id) {
          <div class="rounded-xl border border-cloud bg-white shadow-sm px-4 py-3 flex items-center justify-between gap-3">
            <span class="text-sm text-ink min-w-0 truncate">{{ con.title }}</span>
            <div class="flex items-center gap-4 shrink-0 text-xs font-mono text-muted">
              <span>{{ total(con.assets) }} cards{{ pending(con.assets) ? ' · ' + pending(con.assets) + ' draft' : '' }}</span>
              <span>{{ total(con.items) }} questions{{ pending(con.items) ? ' · ' + pending(con.items) + ' draft' : '' }}</span>
            </div>
          </div>
        } @empty {
          <p class="text-muted text-sm">No concepts in this chapter yet.</p>
        }
      </div>

      <p class="text-xs text-muted mt-8">Publishing takes every draft and reviewed card and question straight to live. Unpublishing retires live content so learners no longer see it — nothing is deleted.</p>
    } @else {
      <p class="text-muted mt-6">Couldn't load this chapter.</p>
    }
  `,
})
export default class ChapterPublishComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly curriculum = inject(CurriculumService);

  private readonly chapterId = this.route.snapshot.paramMap.get('id') ?? '';
  readonly loading = signal(true);
  readonly busy = signal(false);
  readonly content = signal<ChapterContent | null>(null);
  readonly message = signal('');

  readonly chapterTitle = computed(
    () => (this.curriculum.chapters() ?? []).find((c) => c.id === this.chapterId)?.title ?? 'This chapter',
  );

  async ngOnInit(): Promise<void> {
    await this.reload();
  }

  private async reload(): Promise<void> {
    this.loading.set(true);
    try {
      this.content.set(await this.curriculum.getChapterContent(this.chapterId));
    } catch {
      this.content.set(null);
    } finally {
      this.loading.set(false);
    }
  }

  async publish(): Promise<void> {
    this.busy.set(true);
    try {
      const r = await this.curriculum.publishChapter(this.chapterId);
      this.message.set(`Published ${r.assets} cards and ${r.items} questions.`);
      await this.reload();
    } finally {
      this.busy.set(false);
    }
  }

  async retire(): Promise<void> {
    this.busy.set(true);
    try {
      const r = await this.curriculum.retireChapter(this.chapterId);
      this.message.set(`Unpublished ${r.assets} cards and ${r.items} questions.`);
      await this.reload();
    } finally {
      this.busy.set(false);
    }
  }

  total(c: StatusCounts): number {
    return c.draft + c.reviewed + c.live + c.retired;
  }
  pending(c: StatusCounts): number {
    return c.draft + c.reviewed;
  }
}
