import { Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { JournalService } from '../../core/services/journal.service';

@Component({
  selector: 'app-journal-entry',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    <a routerLink="/journal" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
      &larr; Back to journal
    </a>

    @if (notFound()) {
      <p class="text-muted mt-6">This entry couldn't be found.</p>
    } @else {
      <div class="max-w-2xl mx-auto mt-6">
        <div class="flex items-baseline justify-between gap-4">
          <h1 class="font-display text-3xl">{{ entryId() ? 'Journal Entry' : 'New Entry' }}</h1>
          <span class="text-xs text-muted font-mono">{{ headerDate() | date: 'mediumDate' }}</span>
        </div>
        @if (autosaveStatus()) {
          <p class="text-xs text-muted font-mono mt-1">{{ autosaveStatus() }}</p>
        }

        <div class="flex flex-col gap-8 mt-8">
          <label class="flex flex-col gap-2">
            <span class="text-sm font-medium text-muted">Give this entry a title</span>
            <input
              type="text"
              placeholder="e.g. Why ice floats"
              [value]="title()"
              (input)="title.set($any($event.target).value)"
              (blur)="onFieldBlur()"
              class="rounded-xl border border-cloud bg-paper px-3 py-2.5 font-display text-xl focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors"
            />
          </label>

          <label class="flex flex-col gap-2">
            <span class="text-sm font-medium text-muted">What did you learn today?</span>
            <textarea
              rows="4"
              placeholder="Something new you noticed or figured out..."
              [value]="whatILearned()"
              (input)="whatILearned.set($any($event.target).value)"
              (blur)="onFieldBlur()"
              class="rounded-xl border border-cloud bg-paper px-4 py-3 leading-relaxed resize-y focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors"
            ></textarea>
          </label>

          <label class="flex flex-col gap-2">
            <span class="text-sm font-medium text-muted">Why do you think that's true?</span>
            <textarea
              rows="4"
              placeholder="What makes you believe it..."
              [value]="whyIThinkItsTrue()"
              (input)="whyIThinkItsTrue.set($any($event.target).value)"
              (blur)="onFieldBlur()"
              class="rounded-xl border border-cloud bg-paper px-4 py-3 leading-relaxed resize-y focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors"
            ></textarea>
          </label>

          <label class="flex flex-col gap-2">
            <span class="text-sm font-medium text-muted">Can you think of your own example?</span>
            <textarea
              rows="4"
              placeholder="A time this showed up in your own life..."
              [value]="myOwnExample()"
              (input)="myOwnExample.set($any($event.target).value)"
              (blur)="onFieldBlur()"
              class="rounded-xl border border-cloud bg-paper px-4 py-3 leading-relaxed resize-y focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors"
            ></textarea>
          </label>

          <label class="flex flex-col gap-2">
            <span class="text-sm font-medium text-muted">What questions do you still have?</span>
            <textarea
              rows="3"
              placeholder="Anything that's still puzzling..."
              [value]="questionsIHave()"
              (input)="questionsIHave.set($any($event.target).value)"
              (blur)="onFieldBlur()"
              class="rounded-xl border border-cloud bg-paper px-4 py-3 leading-relaxed resize-y focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors"
            ></textarea>
          </label>

          <label class="flex flex-col gap-2">
            <span class="text-sm font-medium text-muted">What will you try tomorrow?</span>
            <textarea
              rows="3"
              placeholder="One small thing to try next..."
              [value]="whatIllTryTomorrow()"
              (input)="whatIllTryTomorrow.set($any($event.target).value)"
              (blur)="onFieldBlur()"
              class="rounded-xl border border-cloud bg-paper px-4 py-3 leading-relaxed resize-y focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors"
            ></textarea>
          </label>
        </div>
      </div>
    }
  `,
})
export default class JournalEntryComponent implements OnInit, OnDestroy {
  private readonly journal = inject(JournalService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly entryId = signal<string | undefined>(this.route.snapshot.paramMap.get('id') ?? undefined);
  readonly notFound = signal(false);

  readonly title = signal('');
  readonly whatILearned = signal('');
  readonly whyIThinkItsTrue = signal('');
  readonly myOwnExample = signal('');
  readonly questionsIHave = signal('');
  readonly whatIllTryTomorrow = signal('');

  private readonly savedDate = signal<string | undefined>(undefined);
  readonly headerDate = computed(() => this.savedDate() ?? new Date().toISOString().slice(0, 10));
  readonly autosaveStatus = signal<string | null>(null);

  ngOnInit(): void {
    const id = this.entryId();
    if (!id) return;

    const entry = this.journal.getById(id);
    if (!entry) {
      this.notFound.set(true);
      return;
    }

    this.title.set(entry.title);
    this.whatILearned.set(entry.whatILearned);
    this.whyIThinkItsTrue.set(entry.whyIThinkItsTrue);
    this.myOwnExample.set(entry.myOwnExample);
    this.questionsIHave.set(entry.questionsIHave);
    this.whatIllTryTomorrow.set(entry.whatIllTryTomorrow);
    this.savedDate.set(entry.date);
  }

  ngOnDestroy(): void {
    this.onFieldBlur();
  }

  onFieldBlur(): void {
    if (this.notFound()) return;

    const draft = {
      title: this.title(),
      whatILearned: this.whatILearned(),
      whyIThinkItsTrue: this.whyIThinkItsTrue(),
      myOwnExample: this.myOwnExample(),
      questionsIHave: this.questionsIHave(),
      whatIllTryTomorrow: this.whatIllTryTomorrow(),
    };
    const hasContent = Object.values(draft).some((v) => v.trim().length > 0);
    if (!hasContent) return;

    const id = this.entryId();
    if (!id) {
      const entry = this.journal.create(draft);
      this.entryId.set(entry.id);
      this.savedDate.set(entry.date);
      void this.router.navigate(['/journal', entry.id], { replaceUrl: true });
    } else {
      this.journal.update(id, draft);
    }
    this.autosaveStatus.set(`Saved ${new Date().toLocaleTimeString()}`);
  }
}
