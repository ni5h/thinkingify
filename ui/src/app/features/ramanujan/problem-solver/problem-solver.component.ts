import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { marked } from 'marked';
import { MathService } from '../../../core/services/math.service';
import { MathProblemDetail } from '../../../core/models/math';
import { MathCoachPanelComponent } from './math-coach-panel/math-coach-panel.component';

@Component({
  selector: 'app-problem-solver',
  standalone: true,
  imports: [RouterLink, MathCoachPanelComponent],
  template: `
    <a routerLink="/ramanujan" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
      &larr; Back to Ramanujan
    </a>

    @if (loading()) {
      <p class="text-muted mt-6">Loading&hellip;</p>
    } @else if (!problem()) {
      <p class="text-muted mt-6">Couldn't find that problem.</p>
    } @else {
      <div class="md:flex md:gap-6 mt-4">
        <div class="md:flex-1 min-w-0">
          <h1 class="font-display text-2xl text-ink">{{ problem()!.title }}</h1>
          <div class="markdown-content text-lg text-ink/90 mt-4 max-w-prose" [innerHTML]="renderedStatement()"></div>

          @if (!solved()) {
            <div class="mt-6 max-w-sm">
              <label class="text-sm font-medium text-muted">Your answer</label>
              <div class="flex gap-2 mt-1">
                <input
                  type="text"
                  [value]="answerInput()"
                  (input)="answerInput.set($any($event.target).value)"
                  (keydown.enter)="submit()"
                  [disabled]="checking()"
                  placeholder="Try to solve it in your head first"
                  class="flex-1 rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors"
                />
                <button
                  type="button"
                  (click)="submit()"
                  [disabled]="checking() || !answerInput().trim()"
                  class="rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors disabled:opacity-60"
                >
                  {{ checking() ? 'Checking…' : 'Check' }}
                </button>
              </div>
              @if (wrongMessage()) {
                <p class="text-amber text-sm mt-2">{{ wrongMessage() }}</p>
              }
            </div>
          } @else {
            <div class="mt-6 rounded-2xl border border-moss/30 bg-moss/5 shadow-sm p-5 max-w-prose">
              <h2 class="font-display text-lg text-ink">You solved it! 🎉</h2>
              <p class="text-sm text-muted mt-1">Here's one neat way to think about it:</p>
              <div class="markdown-content text-ink mt-3" [innerHTML]="renderedSolution()"></div>
            </div>
          }
        </div>

        <aside class="md:w-96 shrink-0 mt-8 md:mt-0 md:h-[32rem]">
          <app-math-coach-panel [problemId]="problem()!.id" [sessionId]="coachSessionId" />
        </aside>
      </div>
    }
  `,
})
export default class ProblemSolverComponent implements OnInit {
  private readonly math = inject(MathService);
  private readonly route = inject(ActivatedRoute);

  readonly coachSessionId = crypto.randomUUID();

  readonly problem = signal<MathProblemDetail | null>(null);
  readonly loading = signal(true);
  readonly answerInput = signal('');
  readonly checking = signal(false);
  readonly wrongMessage = signal<string | null>(null);
  readonly solved = signal(false);
  private readonly solutionMarkdown = signal('');

  readonly renderedStatement = computed(() => {
    const p = this.problem();
    return p ? (marked.parse(p.statement_markdown, { async: false }) as string) : '';
  });
  readonly renderedSolution = computed(() =>
    this.solutionMarkdown() ? (marked.parse(this.solutionMarkdown(), { async: false }) as string) : ''
  );

  async ngOnInit(): Promise<void> {
    const slug = this.route.snapshot.paramMap.get('slug')!;
    this.problem.set((await this.math.getPublishedBySlug(slug)) ?? null);
    this.loading.set(false);
  }

  async submit(): Promise<void> {
    const answer = this.answerInput().trim();
    const problem = this.problem();
    if (!answer || !problem || this.checking()) return;

    this.checking.set(true);
    this.wrongMessage.set(null);
    try {
      const attempt = await this.math.submitAttempt(problem.id, answer);
      if (attempt.is_correct) {
        this.solutionMarkdown.set(attempt.solution_markdown ?? '');
        this.solved.set(true);
      } else {
        this.wrongMessage.set("Not quite — have another think. Your coach can help if you're stuck.");
      }
    } catch {
      this.wrongMessage.set('Something went wrong checking that. Try again in a moment.');
    } finally {
      this.checking.set(false);
    }
  }
}
