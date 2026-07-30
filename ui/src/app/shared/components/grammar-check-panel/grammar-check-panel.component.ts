import { Component, EventEmitter, Input, Output, computed, inject, signal } from '@angular/core';
import { GrammarService } from '../../../core/services/grammar.service';
import { GrammarFlag } from '../../../core/models/grammar';

const VISIBLE_PAGE_SIZE = 2;

/**
 * Smart, like SpellingCheckPanelComponent — injects GrammarService
 * directly and owns the attempt/override HTTP lifecycle. Differs from
 * the spelling panel in interaction shape, not just content: the kid
 * rewrites the whole flagged sentence in a textarea (pre-filled with the
 * original) rather than typing one word, and the concept's rule +
 * example pairs are always visible from the first flag — no escalating
 * hint ladder, no reveal-the-answer step, since grammar fixes aren't a
 * single objectively-correct string the way a spelling is.
 */
@Component({
  selector: 'app-grammar-check-panel',
  standalone: true,
  template: `
    <div class="rounded-2xl border border-cloud bg-white shadow-sm p-4 flex flex-col gap-4">
      <div>
        <h2 class="font-display text-xl text-ink">Let's look at these sentences</h2>
        <p class="text-sm text-muted mt-1">
          Found {{ pending().length }} sentence{{ pending().length === 1 ? '' : 's' }} to look at before this is
          ready to share.
        </p>
      </div>

      @for (flag of visibleFlags(); track flag.id) {
        <div class="rounded-xl border border-cloud bg-paper p-3 flex flex-col gap-2">
          <p class="text-sm font-medium text-ink">{{ flag.concept_label }}</p>
          <p class="text-sm text-muted">{{ flag.concept_rule }}</p>

          @for (example of flag.example_pairs; track example.incorrect) {
            <p class="text-xs text-muted italic">
              &ldquo;{{ example.incorrect }}&rdquo; &rarr; &ldquo;{{ example.correct }}&rdquo;
            </p>
          }

          <p class="text-sm text-ink mt-1">
            Your sentence: <span class="italic">&ldquo;{{ flag.sentence }}&rdquo;</span>
          </p>

          <textarea
            rows="2"
            [value]="attemptInput(flag.id)"
            (input)="setAttemptInput(flag.id, $any($event.target).value)"
            [disabled]="submitting()[flag.id]"
            class="rounded-lg border border-cloud bg-white px-3 py-1.5 text-sm resize-y focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors"
          ></textarea>

          <div class="flex flex-wrap items-center gap-2">
            <button
              type="button"
              (click)="submitAttempt(flag)"
              [disabled]="submitting()[flag.id] || !attemptInput(flag.id).trim()"
              class="rounded-lg bg-moss px-3 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors disabled:opacity-60"
            >
              Try this rewrite
            </button>
            @if (flag.attempt_count >= 2) {
              <button
                type="button"
                (click)="submitOverride(flag)"
                [disabled]="submitting()[flag.id]"
                class="rounded-lg px-3 py-1.5 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors"
              >
                Keep it as is
              </button>
            }
          </div>

          @if (attemptErrors()[flag.id]) {
            <p class="text-amber text-xs">{{ attemptErrors()[flag.id] }}</p>
          }
        </div>
      }

      @if (remainingCount() > 0) {
        <button
          type="button"
          (click)="showMore()"
          class="self-start rounded-lg px-3 py-1.5 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors"
        >
          Show {{ remainingCount() }} more
        </button>
      }
    </div>
  `,
})
export class GrammarCheckPanelComponent {
  @Input({ required: true }) set flags(value: GrammarFlag[]) {
    this.pending.set(value);
    this.visibleCount.set(VISIBLE_PAGE_SIZE);
    // Rewrites start from the original sentence, not blank — the kid
    // edits in place rather than retyping the whole thing from scratch.
    const seeded: Record<string, string> = {};
    for (const flag of value) seeded[flag.id] = this.attemptInputs()[flag.id] ?? flag.sentence;
    this.attemptInputs.set(seeded);
  }
  @Input({ required: true }) contentId!: string;

  @Output() correctionApplied = new EventEmitter<{ oldSentence: string; newSentence: string }>();
  @Output() allResolved = new EventEmitter<void>();

  private readonly grammar = inject(GrammarService);

  readonly pending = signal<GrammarFlag[]>([]);
  readonly visibleCount = signal(VISIBLE_PAGE_SIZE);
  private readonly attemptInputs = signal<Record<string, string>>({});
  readonly submitting = signal<Record<string, boolean>>({});
  readonly attemptErrors = signal<Record<string, string>>({});

  readonly visibleFlags = computed(() => this.pending().slice(0, this.visibleCount()));
  readonly remainingCount = computed(() => Math.max(0, this.pending().length - this.visibleCount()));

  attemptInput(flagId: string): string {
    return this.attemptInputs()[flagId] ?? '';
  }

  setAttemptInput(flagId: string, value: string): void {
    this.attemptInputs.update((map) => ({ ...map, [flagId]: value }));
  }

  showMore(): void {
    this.visibleCount.update((count) => count + VISIBLE_PAGE_SIZE);
  }

  async submitAttempt(flag: GrammarFlag): Promise<void> {
    const attempt = this.attemptInput(flag.id).trim();
    if (!attempt || this.submitting()[flag.id]) return;

    this.submitting.update((map) => ({ ...map, [flag.id]: true }));
    this.attemptErrors.update((map) => ({ ...map, [flag.id]: '' }));

    try {
      const updated = await this.grammar.attemptFix(this.contentId, flag.id, attempt);
      if (updated.status === 'self_corrected') {
        this.correctionApplied.emit({ oldSentence: flag.sentence, newSentence: attempt });
        this.removeResolved(flag.id);
      } else {
        this.pending.update((list) => list.map((f) => (f.id === flag.id ? updated : f)));
      }
    } catch {
      this.attemptErrors.update((map) => ({
        ...map,
        [flag.id]: "Couldn't check that just now — try again in a moment.",
      }));
    } finally {
      this.submitting.update((map) => ({ ...map, [flag.id]: false }));
    }
  }

  async submitOverride(flag: GrammarFlag): Promise<void> {
    if (this.submitting()[flag.id]) return;
    this.submitting.update((map) => ({ ...map, [flag.id]: true }));
    this.attemptErrors.update((map) => ({ ...map, [flag.id]: '' }));

    try {
      await this.grammar.override(this.contentId, flag.id);
      this.removeResolved(flag.id);
    } catch {
      this.attemptErrors.update((map) => ({
        ...map,
        [flag.id]: "Couldn't save that just now — try again in a moment.",
      }));
    } finally {
      this.submitting.update((map) => ({ ...map, [flag.id]: false }));
    }
  }

  private removeResolved(flagId: string): void {
    this.pending.update((list) => list.filter((f) => f.id !== flagId));
    if (this.pending().length === 0) {
      this.allResolved.emit();
    }
  }
}
