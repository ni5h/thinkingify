import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink, ActivatedRoute, Router } from '@angular/router';
import { CurriculumService } from '../../../core/services/curriculum.service';
import {
  CurriculumStatus,
  ITEM_KINDS,
  ITEM_KIND_LABELS,
  ItemKind,
  STATUS_LABELS,
} from '../../../core/models/curriculum';

const INPUT = 'rounded-xl border border-cloud bg-paper px-3 py-2.5 text-sm focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors';
const LABEL = 'flex flex-col gap-1';

@Component({
  selector: 'app-item-editor',
  standalone: true,
  imports: [RouterLink],
  template: `
    <a routerLink="/studio/curriculum/items" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">&larr; Items</a>
    <h1 class="font-display text-3xl mt-4">{{ itemId ? 'Edit item' : 'New item' }}</h1>

    @if (itemId && status()) {
      <div class="mt-3 flex items-center gap-3">
        <span class="text-sm text-muted">Status:</span>
        <span class="rounded-lg bg-cloud-soft px-2.5 py-0.5 text-xs font-medium text-ink">{{ statusLabels[status()!] }}</span>
        @for (action of actionsFor(status()!); track action.key) {
          <button type="button" (click)="act(action.key)" class="rounded-lg bg-moss/10 px-3 py-1 text-sm font-medium text-moss-dark hover:bg-moss/20 transition-colors">{{ action.label }}</button>
        }
      </div>
    }

    <div class="flex flex-col gap-5 mt-6 max-w-xl">
      <label class="${LABEL}">
        <span class="text-sm font-medium text-muted">Concept</span>
        <select class="${INPUT}" [value]="conceptId()" (change)="conceptId.set($any($event.target).value)">
          <option value="">Choose a concept…</option>
          @for (c of concepts(); track c.id) { <option [value]="c.id">{{ c.title }}</option> }
        </select>
      </label>

      <div class="grid grid-cols-2 gap-4">
        <label class="${LABEL}">
          <span class="text-sm font-medium text-muted">Kind</span>
          <select class="${INPUT}" [value]="kind()" (change)="kind.set($any($event.target).value)">
            @for (k of kinds; track k) { <option [value]="k">{{ kindLabels[k] }}</option> }
          </select>
        </label>
        <label class="${LABEL}">
          <span class="text-sm font-medium text-muted">Difficulty</span>
          <input type="number" min="1" max="5" class="${INPUT}" [value]="difficulty()" (input)="difficulty.set(+$any($event.target).value)" />
        </label>
      </div>

      <label class="${LABEL}">
        <span class="text-sm font-medium text-muted">Skill <span class="font-normal">(optional)</span></span>
        <select class="${INPUT}" [value]="skillId()" (change)="skillId.set($any($event.target).value)">
          <option value="">None</option>
          @for (s of skills(); track s.id) { <option [value]="s.id">{{ s.name }}</option> }
        </select>
      </label>

      <label class="${LABEL}">
        <span class="text-sm font-medium text-muted">Question / body</span>
        <textarea rows="4" class="${INPUT} resize-y" [value]="body()" (input)="body.set($any($event.target).value)"></textarea>
      </label>

      <label class="${LABEL}">
        <span class="text-sm font-medium text-muted">Answer key <span class="font-normal">(never shown to learners)</span></span>
        <input class="${INPUT}" [value]="answerKey()" (input)="answerKey.set($any($event.target).value)" />
      </label>

      @if (error()) { <p class="text-amber text-sm">{{ error() }}</p> }

      <div class="flex gap-3">
        <button type="button" (click)="save()" [disabled]="saving() || !conceptId()" class="rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors disabled:opacity-60">
          {{ saving() ? 'Saving…' : 'Save' }}
        </button>
      </div>
    </div>
  `,
})
export default class ItemEditorComponent implements OnInit {
  private readonly curriculum = inject(CurriculumService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly itemId = this.route.snapshot.paramMap.get('id') ?? undefined;
  readonly kinds = ITEM_KINDS;
  readonly kindLabels = ITEM_KIND_LABELS;
  readonly statusLabels = STATUS_LABELS;

  readonly concepts = computed(() => this.curriculum.concepts() ?? []);
  readonly skills = computed(() => this.curriculum.skills() ?? []);

  readonly conceptId = signal('');
  readonly skillId = signal('');
  readonly kind = signal<ItemKind>('apply');
  readonly difficulty = signal(1);
  readonly body = signal('');
  readonly answerKey = signal('');
  readonly status = signal<CurriculumStatus | null>(null);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    if (!this.itemId) return;
    const item = await this.curriculum.getItem(this.itemId);
    if (!item) return;
    this.conceptId.set(item.concept_id);
    this.skillId.set(item.skill_id ?? '');
    this.kind.set(item.kind);
    this.difficulty.set(item.difficulty);
    this.body.set(item.body);
    this.answerKey.set(item.answer_key ?? '');
    this.status.set(item.status);
  }

  actionsFor(status: CurriculumStatus): { key: string; label: string }[] {
    switch (status) {
      case 'draft': return [{ key: 'submit-for-review', label: 'Submit for review' }];
      case 'reviewed': return [{ key: 'accept', label: 'Accept (go live)' }, { key: 'back-to-draft', label: 'Back to draft' }];
      case 'live': return [{ key: 'retire', label: 'Retire' }];
      case 'retired': return [{ key: 'restore', label: 'Restore' }];
    }
  }

  async act(action: string): Promise<void> {
    if (!this.itemId) return;
    try {
      await this.curriculum.transitionItem(this.itemId, action);
      const item = await this.curriculum.getItem(this.itemId);
      this.status.set(item?.status ?? null);
    } catch (err) {
      this.error.set(this.detail(err));
    }
  }

  async save(): Promise<void> {
    this.saving.set(true);
    this.error.set(null);
    const draft = {
      concept_id: this.conceptId(),
      skill_id: this.skillId() || null,
      kind: this.kind(),
      difficulty: this.difficulty(),
      body: this.body(),
      answer_key: this.answerKey() || null,
    };
    try {
      if (this.itemId) {
        await this.curriculum.updateItem(this.itemId, draft);
      } else {
        await this.curriculum.createItem(draft);
      }
      await this.router.navigate(['/studio/curriculum/items']);
    } catch (err) {
      this.error.set(this.detail(err));
    } finally {
      this.saving.set(false);
    }
  }

  private detail(err: unknown): string {
    return (err as { error?: { detail?: string } })?.error?.detail ?? 'Could not save. Please try again.';
  }
}
