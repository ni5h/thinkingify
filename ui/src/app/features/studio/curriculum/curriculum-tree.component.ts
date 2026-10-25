import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CurriculumService } from '../../../core/services/curriculum.service';
import { Chapter, Concept } from '../../../core/models/curriculum';

const INPUT = 'rounded-xl border border-cloud bg-paper px-3 py-2 text-sm focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors';
const BTN = 'rounded-xl bg-moss px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors disabled:opacity-60';
const GHOST = 'rounded-lg px-2.5 py-1 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors';

@Component({
  selector: 'app-curriculum-tree',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="flex items-center justify-between gap-4">
      <h1 class="font-display text-3xl">Curriculum</h1>
      <div class="flex gap-2">
        <a routerLink="/studio/curriculum/items" class="rounded-xl border border-cloud bg-paper px-4 py-2 text-sm font-medium text-ink hover:border-moss transition-colors">Items</a>
        <a routerLink="/studio/curriculum/review" class="rounded-xl border border-cloud bg-paper px-4 py-2 text-sm font-medium text-ink hover:border-moss transition-colors">Review queue</a>
      </div>
    </div>

    <!-- Add subject -->
    <div class="mt-6 flex flex-wrap items-center gap-2">
      <input class="${INPUT}" placeholder="New subject name" [value]="subjectName()" (input)="subjectName.set($any($event.target).value)" />
      <input class="${INPUT} w-32" placeholder="code" [value]="subjectCode()" (input)="subjectCode.set($any($event.target).value)" />
      <button type="button" class="${BTN}" [disabled]="!subjectName().trim() || !subjectCode().trim()" (click)="addSubject()">Add subject</button>
    </div>

    @for (subject of subjects(); track subject.id) {
      <section class="mt-8">
        <div class="flex items-baseline gap-2">
          <h2 class="font-display text-xl text-ink">{{ subject.name }}</h2>
          <span class="text-xs font-mono text-muted">{{ subject.code }}</span>
        </div>

        <!-- Chapters -->
        <div class="mt-3 flex flex-col gap-2">
          @for (chapter of chaptersOf(subject.id); track chapter.id) {
            <div class="rounded-2xl border border-cloud bg-white shadow-sm p-4">
              <div class="flex items-center justify-between gap-3">
                <button type="button" class="flex items-center gap-2 text-left min-w-0" (click)="toggle(chapter.id)">
                  <span class="text-muted w-4">{{ isOpen(chapter.id) ? '▾' : '▸' }}</span>
                  <span class="font-medium text-ink truncate">{{ chapter.title }}</span>
                  <span class="text-xs text-muted shrink-0">{{ conceptsOf(chapter.id).length }} concepts</span>
                </button>
                <a [routerLink]="['/studio/curriculum/chapters', chapter.id, 'publish']" class="${GHOST} shrink-0">Review &amp; publish &rarr;</a>
              </div>

              @if (isOpen(chapter.id)) {
                <ul class="mt-3 ml-6 flex flex-col gap-1.5">
                  @for (concept of conceptsOf(chapter.id); track concept.id) {
                    <li class="flex items-center justify-between gap-3">
                      <span class="text-sm text-ink">{{ concept.title }}</span>
                      <a [routerLink]="['/studio/curriculum/items']" [queryParams]="{ concept: concept.id }" class="${GHOST}">items &rarr;</a>
                    </li>
                  }
                </ul>
                <div class="mt-3 ml-6 flex items-center gap-2">
                  <input class="${INPUT}" placeholder="New concept" [value]="conceptDraft()[chapter.id] ?? ''" (input)="setConceptDraft(chapter.id, $any($event.target).value)" />
                  <button type="button" class="${BTN}" [disabled]="!(conceptDraft()[chapter.id] ?? '').trim()" (click)="addConcept(chapter)">Add concept</button>
                </div>
              }
            </div>
          }
        </div>

        <!-- Add chapter -->
        <div class="mt-3 flex items-center gap-2">
          <input class="${INPUT}" placeholder="New chapter title" [value]="chapterDraft()[subject.id] ?? ''" (input)="setChapterDraft(subject.id, $any($event.target).value)" />
          <button type="button" class="${BTN}" [disabled]="!(chapterDraft()[subject.id] ?? '').trim()" (click)="addChapter(subject.id)">Add chapter</button>
        </div>
      </section>
    } @empty {
      <p class="text-muted mt-8">No subjects yet — add one above to start building the concept map.</p>
    }
  `,
})
export default class CurriculumTreeComponent {
  private readonly curriculum = inject(CurriculumService);

  readonly subjects = computed(() => this.curriculum.subjects() ?? []);
  private readonly allChapters = computed(() => this.curriculum.chapters() ?? []);
  private readonly allConcepts = computed(() => this.curriculum.concepts() ?? []);

  readonly subjectName = signal('');
  readonly subjectCode = signal('');
  readonly chapterDraft = signal<Record<string, string | undefined>>({});
  readonly conceptDraft = signal<Record<string, string | undefined>>({});
  private readonly expanded = signal<Set<string>>(new Set());

  chaptersOf(subjectId: string): Chapter[] {
    return this.allChapters().filter((c) => c.subject_id === subjectId);
  }
  conceptsOf(chapterId: string): Concept[] {
    return this.allConcepts().filter((c) => c.chapter_id === chapterId);
  }
  isOpen(chapterId: string): boolean {
    return this.expanded().has(chapterId);
  }
  toggle(chapterId: string): void {
    this.expanded.update((s) => {
      const next = new Set(s);
      next.has(chapterId) ? next.delete(chapterId) : next.add(chapterId);
      return next;
    });
  }

  setChapterDraft(subjectId: string, value: string): void {
    this.chapterDraft.update((m) => ({ ...m, [subjectId]: value }));
  }
  setConceptDraft(chapterId: string, value: string): void {
    this.conceptDraft.update((m) => ({ ...m, [chapterId]: value }));
  }

  async addSubject(): Promise<void> {
    await this.curriculum.createSubject({ name: this.subjectName().trim(), code: this.subjectCode().trim() });
    this.subjectName.set('');
    this.subjectCode.set('');
  }
  async addChapter(subjectId: string): Promise<void> {
    const title = (this.chapterDraft()[subjectId] ?? '').trim();
    await this.curriculum.createChapter({ subject_id: subjectId, title, order_index: this.chaptersOf(subjectId).length });
    this.setChapterDraft(subjectId, '');
  }
  async addConcept(chapter: Chapter): Promise<void> {
    const title = (this.conceptDraft()[chapter.id] ?? '').trim();
    await this.curriculum.createConcept({ chapter_id: chapter.id, title, order_index: this.conceptsOf(chapter.id).length });
    this.setConceptDraft(chapter.id, '');
  }
}
