import { Component, OnInit, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { FamilyService } from '../../../core/services/family.service';
import { ParentReport, StageBreakdown } from '../../../core/models/parent-report';

const STYLE_LABELS: Record<string, string> = {
  fairy_tale: 'Fairy Tale',
  news_report: 'News Report',
  diary_entry: 'Diary Entry',
  letter: 'Letter',
  how_to: 'How-To',
  blank: 'Freeform',
};

const STAGE_LABELS: Record<string, string> = {
  spelling: 'Spelling',
  grammar: 'Grammar',
  sentence_framing: 'Sentence Variety',
};

@Component({
  selector: 'app-report-view',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    <a routerLink="/profile" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
      &larr; Back to Profile
    </a>

    @if (loading()) {
      <p class="text-muted mt-6">Loading report&hellip;</p>
    } @else if (error()) {
      <p class="text-amber mt-6">{{ error() }}</p>
    } @else if (report(); as r) {
      <div class="max-w-2xl mt-4 flex flex-col gap-6">
        <div>
          <h1 class="font-display text-3xl text-ink">{{ r.headline }}</h1>
          <p class="text-sm text-muted mt-2">
            "{{ r.content_title || '(untitled)' }}"
            @if (styleLabel(r.style)) { &middot; {{ styleLabel(r.style) }} }
            &middot; {{ r.word_count }} words
            &middot; {{ r.created_at | date: 'mediumDate' }}
          </p>
        </div>

        <section class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
          <h2 class="font-display text-lg text-ink">Creativity &amp; voice</h2>
          <p class="text-sm text-ink mt-2 leading-relaxed">{{ r.creativity_narrative }}</p>
        </section>

        @if (r.went_well.length > 0) {
          <section class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
            <h2 class="font-display text-lg text-ink">What went well</h2>
            <ul class="mt-2 flex flex-col gap-1.5">
              @for (item of r.went_well; track item) {
                <li class="text-sm text-ink flex gap-2"><span class="text-moss">&bull;</span>{{ item }}</li>
              }
            </ul>
          </section>
        }

        @if (r.was_tricky.length > 0) {
          <section class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
            <h2 class="font-display text-lg text-ink">What was tricky</h2>
            <ul class="mt-2 flex flex-col gap-1.5">
              @for (item of r.was_tricky; track item) {
                <li class="text-sm text-ink flex gap-2"><span class="text-amber">&bull;</span>{{ item }}</li>
              }
            </ul>
          </section>
        }

        <section class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
          <h2 class="font-display text-lg text-ink">Stage by stage</h2>
          <div class="mt-3 flex flex-col gap-3">
            @for (stage of stageEntries(r); track stage.key) {
              <div class="rounded-xl bg-paper p-3">
                <div class="flex items-baseline justify-between">
                  <span class="text-sm font-medium text-ink">{{ stage.label }}</span>
                  <span class="text-xs text-muted font-mono">
                    {{ stage.data.found }} found &middot; {{ stage.data.self_corrected }} fixed himself
                    @if (stage.data.ai_assisted > 0) { &middot; {{ stage.data.ai_assisted }} with a hint }
                    @if (stage.data.kept_as_is > 0) { &middot; {{ stage.data.kept_as_is }} kept as-is }
                  </span>
                </div>
                @if (stage.data.concepts.length > 0) {
                  <p class="text-xs text-muted mt-1">{{ stage.data.concepts.join(', ') }}</p>
                }
              </div>
            }
          </div>
        </section>

        <section class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
          <h2 class="font-display text-lg text-ink">AI help level</h2>
          <p class="text-sm text-ink mt-2">{{ r.ai_help_level }}</p>
        </section>

        @if (r.suggested_action) {
          <section class="rounded-2xl border border-moss/30 bg-moss/5 shadow-sm p-5">
            <h2 class="font-display text-lg text-ink">A gentle idea</h2>
            <p class="text-sm text-ink mt-2">{{ r.suggested_action }}</p>
          </section>
        }
      </div>
    }
  `,
})
export default class ReportViewComponent implements OnInit {
  private readonly family = inject(FamilyService);
  private readonly route = inject(ActivatedRoute);

  readonly report = signal<ParentReport | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    const childId = this.route.snapshot.paramMap.get('childId')!;
    const reportId = this.route.snapshot.paramMap.get('reportId')!;
    try {
      this.report.set(await this.family.childReport(childId, reportId));
    } catch {
      this.error.set("Couldn't load this report.");
    } finally {
      this.loading.set(false);
    }
  }

  styleLabel(style: string | null): string {
    return style ? (STYLE_LABELS[style] ?? style) : '';
  }

  stageEntries(report: ParentReport): { key: string; label: string; data: StageBreakdown }[] {
    return Object.entries(report.stage_breakdown).map(([key, data]) => ({
      key,
      label: STAGE_LABELS[key] ?? key,
      data,
    }));
  }
}
