import { Component, HostListener, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { BrotherService } from '../../../core/services/brother.service';
import { BrotherQuestion, BrotherSession } from '../../../core/models/brother';
import { NumericKeypadComponent } from './numeric-keypad/numeric-keypad.component';

type View = 'home' | 'session' | 'summary';
type Feedback = 'correct' | 'incorrect' | null;

const FEEDBACK_MS = 1400;

@Component({
  selector: 'app-brothers',
  standalone: true,
  imports: [RouterLink, NumericKeypadComponent],
  template: `
    <a routerLink="/ramanujan" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">
      &larr; Back to Ramanujan
    </a>

    @if (view() === 'home') {
      <h1 class="font-display text-3xl mt-4">Brothers</h1>
      <p class="text-muted mt-2 max-w-prose">
        A number's "brother" is what it needs to reach the next round number. The brother of
        <b>7</b> is <b>3</b> (7 + 3 = 10); the brother of <b>57</b> is <b>43</b> (57 + 43 = 100).
        Practise these in your head and left-to-right maths gets much easier. Short sessions, no
        clock &mdash; just steady practice.
      </p>

      <div class="mt-8 flex flex-col gap-2 max-w-md">
        @for (tier of state() ?? []; track tier.tier_id) {
          <div class="rounded-xl border border-cloud bg-white shadow-sm px-4 py-3 flex items-center justify-between gap-3">
            <span [class]="tier.status === 'locked' ? 'text-sm text-muted' : 'text-sm text-ink'">{{ tier.name }}</span>
            <span [class]="statusPillClass(tier.status)">{{ statusLabel(tier.status) }}</span>
          </div>
        }
      </div>

      <button
        type="button"
        (click)="startSession()"
        [disabled]="starting()"
        class="mt-8 rounded-xl bg-moss px-6 py-3 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors disabled:opacity-60"
      >
        {{ starting() ? 'Starting…' : 'Start practice' }}
      </button>
      @if (error()) {
        <p class="text-amber text-sm mt-3">{{ error() }}</p>
      }
    }

    @if (view() === 'session' && currentQuestion(); as q) {
      <div class="max-w-md mx-auto mt-6 text-center">
        <p class="text-xs text-muted font-mono">Question {{ questionNumber() }} of {{ total() }}</p>
        <p class="text-sm text-muted mt-6">What's the brother of</p>

        <div class="font-display text-6xl mt-3 tracking-wide">
          <span class="text-muted/40">{{ inertPrefix(q) }}</span><span class="text-ink">{{ activeChunk(q) }}</span>
        </div>

        <div class="mt-6 h-14 flex items-center justify-center">
          @if (feedback() === null) {
            <span class="font-display text-4xl text-moss-dark">{{ currentAnswer() || '·' }}</span>
          } @else if (feedback() === 'correct') {
            <span class="font-display text-4xl text-moss">{{ currentAnswer() }} ✓</span>
          } @else {
            <span class="font-display text-2xl text-muted">You wrote {{ currentAnswer() }} &middot; it's {{ revealedAnswer() }}</span>
          }
        </div>

        <div class="mt-4 flex justify-center">
          <app-numeric-keypad
            [disabled]="feedback() !== null"
            [canSubmit]="currentAnswer().length > 0"
            (digit)="pushDigit($event)"
            (clear)="clearAnswer()"
            (enter)="submit()"
          />
        </div>
      </div>
    }

    @if (view() === 'summary') {
      <div class="max-w-md mx-auto mt-10 rounded-2xl border border-cloud bg-white shadow-sm p-8 text-center">
        <h1 class="font-display text-2xl text-ink">Session done</h1>
        <p class="text-muted mt-2">
          {{ total() }} questions &middot; {{ sessionAccuracyPct() }}% right
        </p>
        @for (msg of tierMessages(); track msg) {
          <p class="text-moss-dark text-sm mt-3">{{ msg }}</p>
        }
        <div class="flex flex-col gap-2 mt-6">
          <button
            type="button"
            (click)="startSession()"
            [disabled]="starting()"
            class="rounded-xl bg-moss px-6 py-3 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors disabled:opacity-60"
          >
            Practise again
          </button>
          <button
            type="button"
            (click)="goHome()"
            class="rounded-xl border border-cloud bg-paper px-6 py-3 text-sm font-medium text-ink hover:border-moss hover:bg-cloud/60 transition-colors"
          >
            Done for now
          </button>
        </div>
      </div>
    }
  `,
})
export default class BrothersComponent {
  private readonly brothers = inject(BrotherService);

  readonly state = this.brothers.state;

  readonly view = signal<View>('home');
  readonly starting = signal(false);
  readonly error = signal<string | null>(null);

  private readonly session = signal<BrotherSession | null>(null);
  private readonly questionIndex = signal(0);
  readonly currentAnswer = signal('');
  readonly feedback = signal<Feedback>(null);
  readonly revealedAnswer = signal<number | null>(null);
  private questionStartMs = 0;

  private correctCount = 0;
  private readonly masteredTierIds = signal<string[]>([]);
  private readonly unlockedTierIds = signal<string[]>([]);

  readonly total = computed(() => this.session()?.questions.length ?? 0);
  readonly questionNumber = computed(() => this.questionIndex() + 1);
  readonly currentQuestion = computed<BrotherQuestion | null>(
    () => this.session()?.questions[this.questionIndex()] ?? null
  );
  readonly sessionAccuracyPct = computed(() =>
    this.total() === 0 ? 0 : Math.round((this.correctCount / this.total()) * 100)
  );

  readonly tierMessages = computed(() => {
    const names = new Map((this.state() ?? []).map((t) => [t.tier_id, t.name]));
    const msgs: string[] = [];
    for (const id of this.masteredTierIds()) msgs.push(`You've mastered ${names.get(id) ?? id}.`);
    for (const id of this.unlockedTierIds()) msgs.push(`New tier unlocked: ${names.get(id) ?? id}.`);
    return msgs;
  });

  statusLabel(status: string): string {
    return status === 'mastered' ? 'Mastered' : status === 'active' ? 'Practising' : 'Locked';
  }

  statusPillClass(status: string): string {
    if (status === 'mastered') return 'rounded-lg bg-moss/10 px-2.5 py-0.5 text-xs font-medium text-moss-dark';
    if (status === 'active') return 'rounded-lg bg-amber/10 px-2.5 py-0.5 text-xs font-medium text-amber';
    return 'rounded-lg bg-cloud/60 px-2.5 py-0.5 text-xs font-medium text-muted';
  }

  private splitNumber(q: BrotherQuestion): { prefix: string; active: string } {
    const s = String(q.number);
    const activeLen = Math.min(q.active_digits, s.length);
    return { prefix: s.slice(0, s.length - activeLen), active: s.slice(s.length - activeLen) };
  }
  inertPrefix(q: BrotherQuestion): string {
    return this.splitNumber(q).prefix;
  }
  activeChunk(q: BrotherQuestion): string {
    return this.splitNumber(q).active;
  }

  async startSession(): Promise<void> {
    this.starting.set(true);
    this.error.set(null);
    try {
      const session = await this.brothers.startSession();
      this.session.set(session);
      this.questionIndex.set(0);
      this.correctCount = 0;
      this.masteredTierIds.set([]);
      this.unlockedTierIds.set([]);
      this.resetQuestion();
      this.view.set('session');
    } catch {
      this.error.set('Could not start a session. Please try again.');
    } finally {
      this.starting.set(false);
    }
  }

  private resetQuestion(): void {
    this.currentAnswer.set('');
    this.feedback.set(null);
    this.revealedAnswer.set(null);
    this.questionStartMs = Date.now();
  }

  pushDigit(d: string): void {
    if (this.feedback() !== null) return;
    if (this.currentAnswer().length >= 4) return;
    this.currentAnswer.update((v) => v + d);
  }

  clearAnswer(): void {
    if (this.feedback() !== null) return;
    this.currentAnswer.set('');
  }

  async submit(): Promise<void> {
    const session = this.session();
    const q = this.currentQuestion();
    if (!session || !q || this.feedback() !== null || this.currentAnswer().length === 0) return;

    const responseMs = Date.now() - this.questionStartMs;
    const userAnswer = Number(this.currentAnswer());
    try {
      const result = await this.brothers.answer(session.id, q.index, userAnswer, responseMs);
      if (result.correct) this.correctCount += 1;
      if (result.mastered_tier_id) this.masteredTierIds.update((l) => [...l, result.mastered_tier_id!]);
      if (result.unlocked_tier_id) this.unlockedTierIds.update((l) => [...l, result.unlocked_tier_id!]);
      this.feedback.set(result.correct ? 'correct' : 'incorrect');
      this.revealedAnswer.set(result.correct_answer);
      setTimeout(() => this.advance(), FEEDBACK_MS);
    } catch {
      this.error.set('Something went wrong. Please try again.');
    }
  }

  private advance(): void {
    if (this.questionIndex() + 1 >= this.total()) {
      this.brothers.reloadState();
      this.view.set('summary');
      return;
    }
    this.questionIndex.update((i) => i + 1);
    this.resetQuestion();
  }

  goHome(): void {
    this.view.set('home');
  }

  @HostListener('document:keydown', ['$event'])
  onKey(event: KeyboardEvent): void {
    if (this.view() !== 'session') return;
    if (event.key >= '0' && event.key <= '9') {
      this.pushDigit(event.key);
    } else if (event.key === 'Backspace') {
      this.currentAnswer.update((v) => v.slice(0, -1));
    } else if (event.key === 'Enter') {
      void this.submit();
    }
  }
}
