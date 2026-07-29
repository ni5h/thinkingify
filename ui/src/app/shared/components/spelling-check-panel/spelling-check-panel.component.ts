import { Component, EventEmitter, Input, Output, computed, inject, signal } from '@angular/core';
import { SpellingService } from '../../../core/services/spelling.service';
import { SpellingFlag } from '../../../core/models/spelling';

const VISIBLE_PAGE_SIZE = 2;

/**
 * Smart, like CompanionPanelComponent — injects SpellingService directly
 * and owns the attempt/override HTTP lifecycle. Surfaces at most a couple
 * of flags at a time even if more exist (per the app's evaluation-pipeline
 * spec), rather than dumping the whole list on the kid at once.
 *
 * The parent decides *when* to show this (a mandatory gate before publish/
 * submit), and reacts to `correctionApplied` to push the fix into its own
 * live editor content, and to `allResolved` to let the real publish call
 * through — this component never touches the editor or the publish flow
 * itself.
 */
@Component({
  selector: 'app-spelling-check-panel',
  standalone: true,
  template: `
    <div class="rounded-2xl border border-cloud bg-white shadow-sm p-4 flex flex-col gap-4">
      <div>
        <h2 class="font-display text-xl text-ink">Let's check your spelling</h2>
        <p class="text-sm text-muted mt-1">
          Found {{ pending().length }} word{{ pending().length === 1 ? '' : 's' }} to look at before this is
          ready to share.
        </p>
      </div>

      @for (flag of visibleFlags(); track flag.id) {
        <div class="rounded-xl border border-cloud bg-paper p-3 flex flex-col gap-2">
          <p class="text-sm text-ink">
            <span class="font-mono font-medium">{{ flag.word }}</span>
            &mdash; <span class="text-muted italic">&ldquo;{{ flag.context_sentence }}&rdquo;</span>
          </p>

          @if (flag.hint) {
            <p class="text-sm text-muted">{{ flag.hint }}</p>
          }

          @if (flag.hint_revealed) {
            <p class="text-sm text-moss-dark">
              Here's one to try: <span class="font-mono font-medium">{{ flag.suggested_correction }}</span>
            </p>
          }

          <div class="flex flex-wrap items-center gap-2">
            <input
              type="text"
              [value]="attemptInput(flag.id)"
              (input)="setAttemptInput(flag.id, $any($event.target).value)"
              (keydown.enter)="submitAttempt(flag)"
              [disabled]="submitting()[flag.id]"
              class="flex-1 min-w-[8rem] rounded-lg border border-cloud bg-white px-3 py-1.5 text-sm focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors"
            />
            <button
              type="button"
              (click)="submitAttempt(flag)"
              [disabled]="submitting()[flag.id] || !attemptInput(flag.id).trim()"
              class="rounded-lg bg-moss px-3 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors disabled:opacity-60"
            >
              {{ flag.hint_revealed ? 'Apply' : 'Try it' }}
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
export class SpellingCheckPanelComponent {
  @Input({ required: true }) set flags(value: SpellingFlag[]) {
    this.pending.set(value);
    this.visibleCount.set(VISIBLE_PAGE_SIZE);
  }
  @Input({ required: true }) contentId!: string;

  @Output() correctionApplied = new EventEmitter<{ oldWord: string; newWord: string }>();
  @Output() allResolved = new EventEmitter<void>();

  private readonly spelling = inject(SpellingService);

  readonly pending = signal<SpellingFlag[]>([]);
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

  async submitAttempt(flag: SpellingFlag): Promise<void> {
    const attempt = this.attemptInput(flag.id).trim();
    if (!attempt || this.submitting()[flag.id]) return;

    this.submitting.update((map) => ({ ...map, [flag.id]: true }));
    this.attemptErrors.update((map) => ({ ...map, [flag.id]: '' }));

    try {
      const updated = await this.spelling.attemptFix(this.contentId, flag.id, attempt);
      if (updated.status === 'self_corrected') {
        this.correctionApplied.emit({ oldWord: flag.word, newWord: attempt });
        this.removeResolved(flag.id);
      } else {
        this.pending.update((list) => list.map((f) => (f.id === flag.id ? updated : f)));
        this.setAttemptInput(flag.id, updated.hint_revealed ? updated.suggested_correction ?? '' : '');
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

  async submitOverride(flag: SpellingFlag): Promise<void> {
    if (this.submitting()[flag.id]) return;
    this.submitting.update((map) => ({ ...map, [flag.id]: true }));
    this.attemptErrors.update((map) => ({ ...map, [flag.id]: '' }));

    try {
      await this.spelling.override(this.contentId, flag.id);
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
