import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ConceptProgress, LearnConcept, LearnService } from '../../../core/services/learn.service';

interface TrailConcept extends LearnConcept {
  state: ConceptProgress['state'];
  available: boolean;
  mastered: boolean;
}

@Component({
  selector: 'app-learn-landing',
  standalone: true,
  imports: [RouterLink],
  template: `
    <a [routerLink]="roomPath" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">&larr; {{ roomName }}</a>
    <h1 class="font-display text-3xl mt-4">Learn</h1>

    @if (loading()) {
      <p class="text-muted mt-6">Loading…</p>
    } @else if (!chapterTitle()) {
      <div class="mt-6 rounded-2xl border border-cloud bg-white shadow-sm p-6">
        <p class="text-ink font-medium">Nothing here yet.</p>
        <p class="text-muted mt-1">Your chapters will appear once they're ready.</p>
      </div>
    } @else {
      <p class="text-muted mt-1">{{ chapterTitle() }}</p>
      <div class="mt-5 flex flex-col gap-2">
        @for (c of concepts(); track c.id) {
          @if (c.available) {
            <a [routerLink]="[learnPath, c.id]" class="rounded-2xl border border-cloud bg-white shadow-sm p-4 flex items-center justify-between gap-3 hover:border-moss hover:shadow-md transition-all">
              <span class="text-ink font-medium">{{ c.title }}</span>
              <span [class]="badge(c.state)">{{ label(c.state) }}</span>
            </a>
          } @else {
            <div class="rounded-2xl border border-cloud bg-paper p-4 flex items-center justify-between gap-3 opacity-70">
              <span class="text-muted">{{ c.title }}</span>
              <span class="text-xs text-muted">Finish earlier ones first</span>
            </div>
          }
        }
      </div>
    }
  `,
})
export default class LearnLandingComponent implements OnInit {
  private readonly learn = inject(LearnService);
  private readonly route = inject(ActivatedRoute);

  // Which room/subject this landing serves — supplied by the route's `data`.
  readonly subjectCode = (this.route.snapshot.data['subjectCode'] as string) ?? 'maths';
  readonly roomPath = (this.route.snapshot.data['roomPath'] as string) ?? '/ramanujan';
  readonly roomName = (this.route.snapshot.data['roomName'] as string) ?? 'Ramanujan';
  readonly learnPath = (this.route.snapshot.data['learnPath'] as string) ?? '/ramanujan/learn';

  readonly loading = signal(true);
  readonly chapterTitle = signal('');
  readonly concepts = signal<TrailConcept[]>([]);

  async ngOnInit(): Promise<void> {
    try {
      const subjects = await this.learn.getSubjects();
      const subject = subjects.find((s) => s.code === this.subjectCode);
      if (!subject) return;
      const chapters = await this.learn.getChapters(subject.id);
      if (chapters.length === 0) return;
      const chapter = chapters.sort((a, b) => a.order_index - b.order_index)[0];
      this.chapterTitle.set(chapter.title);

      const [concepts, progress] = await Promise.all([
        this.learn.getConcepts(chapter.id),
        this.learn.getProgress(chapter.id),
      ]);
      const byId = new Map(progress.map((p) => [p.concept_id, p]));
      this.concepts.set(
        concepts
          .sort((a, b) => a.order_index - b.order_index)
          .map((c) => {
            const p = byId.get(c.id);
            return { ...c, state: p?.state ?? 'learning', available: p?.available ?? true, mastered: p?.mastered ?? false };
          }),
      );
    } finally {
      this.loading.set(false);
    }
  }

  label(state: ConceptProgress['state']): string {
    return state === 'solid' ? 'Solid' : state === 'needs_look' ? 'Another look' : 'Start';
  }
  badge(state: ConceptProgress['state']): string {
    const base = 'shrink-0 rounded-lg px-2.5 py-0.5 text-xs font-medium';
    if (state === 'solid') return `${base} bg-moss/10 text-moss-dark`;
    if (state === 'needs_look') return `${base} bg-amber/20 text-ink`;
    return `${base} bg-cloud-soft text-muted`;
  }
}
