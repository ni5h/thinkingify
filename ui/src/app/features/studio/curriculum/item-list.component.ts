import { Component, OnInit, computed, inject } from '@angular/core';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { CurriculumService } from '../../../core/services/curriculum.service';
import {
  CURRICULUM_STATUSES,
  CurriculumStatus,
  ITEM_KINDS,
  ITEM_KIND_LABELS,
  ItemKind,
  STATUS_LABELS,
  Item,
} from '../../../core/models/curriculum';

const SELECT = 'rounded-xl border border-cloud bg-paper px-3 py-2 text-sm focus:outline-none focus:border-moss transition-colors';

@Component({
  selector: 'app-item-list',
  standalone: true,
  imports: [RouterLink],
  template: `
    <a routerLink="/studio/curriculum" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">&larr; Curriculum</a>

    <div class="flex items-center justify-between gap-4 mt-4">
      <h1 class="font-display text-3xl">Items</h1>
      <a routerLink="/studio/curriculum/items/new" class="rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors">New item</a>
    </div>

    <!-- Filters -->
    <div class="mt-5 flex flex-wrap gap-2">
      <select class="${SELECT}" [value]="filter().status ?? ''" (change)="setStatus($any($event.target).value)">
        <option value="">Any status</option>
        @for (s of statuses; track s) { <option [value]="s">{{ statusLabels[s] }}</option> }
      </select>
      <select class="${SELECT}" [value]="filter().concept_id ?? ''" (change)="setConcept($any($event.target).value)">
        <option value="">Any concept</option>
        @for (c of concepts(); track c.id) { <option [value]="c.id">{{ c.title }}</option> }
      </select>
      <select class="${SELECT}" [value]="filter().skill_id ?? ''" (change)="setSkill($any($event.target).value)">
        <option value="">Any skill</option>
        @for (s of skills(); track s.id) { <option [value]="s.id">{{ s.name }}</option> }
      </select>
      <select class="${SELECT}" [value]="filter().kind ?? ''" (change)="setKind($any($event.target).value)">
        <option value="">Any kind</option>
        @for (k of kinds; track k) { <option [value]="k">{{ kindLabels[k] }}</option> }
      </select>
    </div>

    <div class="mt-5 flex flex-col gap-2">
      @for (item of items(); track item.id) {
        <div class="rounded-2xl border border-cloud bg-white shadow-sm p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="text-sm text-ink truncate">{{ item.body || '(no text)' }}</p>
              <p class="text-xs text-muted font-mono mt-1">
                {{ kindLabels[item.kind] }} &middot; Lvl {{ item.difficulty }} &middot; {{ conceptTitle(item.concept_id) }}
              </p>
            </div>
            <span [class]="badgeClass(item.status)">{{ statusLabels[item.status] }}</span>
          </div>
          <div class="flex flex-wrap gap-2 mt-3">
            <a [routerLink]="['/studio/curriculum/items', item.id, 'edit']" class="rounded-lg bg-cloud px-3 py-1.5 text-sm font-medium text-ink hover:bg-cloud-soft transition-colors">Edit</a>
            @for (action of actionsFor(item.status); track action.key) {
              <button type="button" (click)="act(item.id, action.key)" class="rounded-lg bg-moss/10 px-3 py-1.5 text-sm font-medium text-moss-dark hover:bg-moss/20 transition-colors">{{ action.label }}</button>
            }
            <button type="button" (click)="remove(item.id)" class="rounded-lg px-3 py-1.5 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">Delete</button>
          </div>
        </div>
      } @empty {
        <p class="text-muted">No items match.</p>
      }
    </div>
  `,
})
export default class ItemListComponent implements OnInit {
  private readonly curriculum = inject(CurriculumService);
  private readonly route = inject(ActivatedRoute);

  readonly statuses = CURRICULUM_STATUSES;
  readonly kinds = ITEM_KINDS;
  readonly statusLabels = STATUS_LABELS;
  readonly kindLabels = ITEM_KIND_LABELS;

  readonly items = computed(() => this.curriculum.items() ?? []);
  readonly concepts = computed(() => this.curriculum.concepts() ?? []);
  readonly skills = computed(() => this.curriculum.skills() ?? []);
  readonly filter = this.curriculum.itemFilter;

  ngOnInit(): void {
    const concept = this.route.snapshot.queryParamMap.get('concept');
    this.curriculum.itemFilter.set(concept ? { concept_id: concept } : {});
  }

  conceptTitle(id: string): string {
    return this.curriculum.conceptsById().get(id)?.title ?? '—';
  }

  private patch(p: Partial<ReturnType<typeof this.filter>>): void {
    this.curriculum.itemFilter.update((f) => ({ ...f, ...p }));
  }
  setStatus(v: string): void { this.patch({ status: (v || undefined) as CurriculumStatus | undefined }); }
  setConcept(v: string): void { this.patch({ concept_id: v || undefined }); }
  setSkill(v: string): void { this.patch({ skill_id: v || undefined }); }
  setKind(v: string): void { this.patch({ kind: (v || undefined) as ItemKind | undefined }); }

  actionsFor(status: CurriculumStatus): { key: string; label: string }[] {
    switch (status) {
      case 'draft': return [{ key: 'submit-for-review', label: 'Submit for review' }];
      case 'reviewed': return [{ key: 'accept', label: 'Accept (go live)' }, { key: 'back-to-draft', label: 'Back to draft' }];
      case 'live': return [{ key: 'retire', label: 'Retire' }];
      case 'retired': return [{ key: 'restore', label: 'Restore' }];
    }
  }

  badgeClass(status: CurriculumStatus): string {
    const base = 'shrink-0 rounded-lg px-2.5 py-0.5 text-xs font-medium';
    if (status === 'live') return `${base} bg-moss/10 text-moss-dark`;
    if (status === 'reviewed') return `${base} bg-amber/20 text-ink`;
    if (status === 'retired') return `${base} bg-cloud text-muted`;
    return `${base} bg-cloud-soft text-muted`;
  }

  async act(id: string, action: string): Promise<void> {
    await this.curriculum.transitionItem(id, action);
  }
  async remove(id: string): Promise<void> {
    if (confirm('Delete this item?')) await this.curriculum.deleteItem(id);
  }
}
