import { Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CurriculumService } from '../../../core/services/curriculum.service';
import { CurriculumStatus, ITEM_KIND_LABELS, STATUS_LABELS } from '../../../core/models/curriculum';

@Component({
  selector: 'app-review-queue',
  standalone: true,
  imports: [RouterLink],
  template: `
    <a routerLink="/studio/curriculum" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">&larr; Curriculum</a>
    <h1 class="font-display text-3xl mt-4">Review queue</h1>
    <p class="text-muted mt-1">Items waiting for a human decision before they go live.</p>

    <div class="mt-6 flex flex-col gap-2">
      @for (item of queue(); track item.id) {
        <div class="rounded-2xl border border-cloud bg-white shadow-sm p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="text-sm text-ink">{{ item.body || '(no text)' }}</p>
              <p class="text-xs text-muted font-mono mt-1">{{ kindLabels[item.kind] }} &middot; {{ conceptTitle(item.concept_id) }}</p>
            </div>
            <span [class]="badge(item.status)">{{ statusLabels[item.status] }}</span>
          </div>
          <div class="flex flex-wrap gap-2 mt-3">
            <a [routerLink]="['/studio/curriculum/items', item.id, 'edit']" class="rounded-lg bg-cloud px-3 py-1.5 text-sm font-medium text-ink hover:bg-cloud-soft transition-colors">Open</a>
            @if (item.status === 'draft') {
              <button type="button" (click)="act(item.id, 'submit-for-review')" class="rounded-lg bg-moss/10 px-3 py-1.5 text-sm font-medium text-moss-dark hover:bg-moss/20 transition-colors">Submit for review</button>
            }
            @if (item.status === 'reviewed') {
              <button type="button" (click)="act(item.id, 'accept')" class="rounded-lg bg-moss/10 px-3 py-1.5 text-sm font-medium text-moss-dark hover:bg-moss/20 transition-colors">Accept (go live)</button>
              <button type="button" (click)="act(item.id, 'back-to-draft')" class="rounded-lg px-3 py-1.5 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">Back to draft</button>
            }
          </div>
        </div>
      } @empty {
        <p class="text-muted">Nothing waiting — the queue is clear.</p>
      }
    </div>
  `,
})
export default class ReviewQueueComponent {
  private readonly curriculum = inject(CurriculumService);

  readonly queue = computed(() => this.curriculum.reviewItems() ?? []);
  readonly kindLabels = ITEM_KIND_LABELS;
  readonly statusLabels = STATUS_LABELS;

  conceptTitle(id: string): string {
    return this.curriculum.conceptsById().get(id)?.title ?? '—';
  }
  badge(status: CurriculumStatus): string {
    const base = 'shrink-0 rounded-lg px-2.5 py-0.5 text-xs font-medium';
    return status === 'reviewed' ? `${base} bg-amber/20 text-ink` : `${base} bg-cloud-soft text-muted`;
  }
  async act(id: string, action: string): Promise<void> {
    await this.curriculum.transitionItem(id, action);
  }
}
