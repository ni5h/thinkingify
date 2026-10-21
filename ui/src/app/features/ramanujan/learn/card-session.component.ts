import { Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import {
  AnswerResult,
  CardData,
  CheckItem,
  CheckSession,
  LearnAsset,
  LearnService,
  RecapData,
} from '../../../core/services/learn.service';

type Step = 'intro' | 'card' | 'recap' | 'check' | 'done';
type ThinkResult = 'right' | 'wrong' | 'unsure';

@Component({
  selector: 'app-card-session',
  standalone: true,
  imports: [RouterLink],
  template: `
    <a [routerLink]="learnPath" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">&larr; Learn</a>

    @if (loading()) {
      <p class="text-muted mt-6">Loading…</p>
    } @else if (error()) {
      <p class="text-amber mt-6">{{ error() }}</p>
    } @else {
      <!-- Trail -->
      <div class="mt-4 flex items-center gap-1.5" role="img" aria-label="Progress">
        @for (d of dots(); track $index) {
          <span [class]="dotClass($index)"></span>
        }
      </div>

      @switch (step()) {
        @case ('intro') {
          <section class="mt-6 rounded-2xl border border-cloud bg-white shadow-sm p-6">
            <p class="text-xs font-mono tracking-wider text-moss-dark">MATHS · CLASS 4</p>
            <h1 class="font-display text-2xl text-ink mt-1">{{ cards().length }} short cards, then a few questions</h1>
            <p class="text-muted mt-2">About 15 minutes. No timer, no score. It's fine to say "not sure".</p>
            <div class="flex flex-wrap gap-3 mt-6">
              <button type="button" (click)="startCards()" class="rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors">Start</button>
              <button type="button" (click)="startCheck('challenge')" class="rounded-xl border border-cloud bg-paper px-5 py-2.5 text-sm font-medium text-ink hover:border-moss transition-colors">I already know this</button>
            </div>
          </section>
        }

        @case ('card') {
          @let card = cards()[cardIx()];
          <section class="mt-6 rounded-2xl border border-cloud bg-white shadow-sm p-6 flex flex-col gap-4">
            <p class="text-xs font-mono tracking-wider text-moss-dark">CARD {{ cardIx() + 1 }} OF {{ cards().length }}</p>
            <h2 class="font-display text-xl text-ink">{{ card.title }}</h2>
            <div class="rounded-2xl bg-moss/10 min-h-28 flex items-center justify-center p-6 text-center">
              <span class="text-sm text-moss-dark/70 font-medium">Illustration for "{{ card.title }}"</span>
            </div>
            <p class="text-lg text-ink leading-relaxed">{{ card.text }}</p>
            <div>
              <button type="button" (click)="toggleAudio(card.audio_script)" class="inline-flex items-center gap-2 rounded-xl border border-moss bg-white px-4 py-2 text-sm font-medium text-ink hover:bg-moss/5 transition-colors">
                {{ speaking() ? '■ Stop' : '▶ Listen' }}
              </button>
            </div>

            <!-- Think first -->
            <div class="rounded-2xl border border-cloud p-4">
              <p class="text-xs font-mono tracking-wider text-muted">THINK FIRST</p>
              <p class="text-ink mt-1">{{ card.think.q }}</p>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-3">
                @for (opt of card.think.options; track $index) {
                  <button type="button" [disabled]="thinkAnswered()" (click)="pickThink($index)" [class]="thinkOptClass($index)">{{ opt }}</button>
                }
              </div>
              @if (!thinkAnswered()) {
                <button type="button" (click)="pickThink(-1)" class="mt-2 rounded-lg px-3 py-1.5 text-sm text-muted hover:bg-cloud/60 hover:text-ink transition-colors">Not sure</button>
              } @else {
                <p class="mt-3 rounded-xl bg-moss/10 p-3 text-sm text-ink"><strong>{{ thinkLead() }}</strong> {{ card.think.why }}</p>
              }
            </div>

            <div class="flex gap-3">
              <button type="button" (click)="nextCard()" class="rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors">Next</button>
            </div>
          </section>
        }

        @case ('recap') {
          <section class="mt-6 rounded-2xl border border-cloud bg-white shadow-sm p-6">
            <p class="text-xs font-mono tracking-wider text-moss-dark">RECAP</p>
            <h2 class="font-display text-xl text-ink mt-1">What we found out</h2>
            <ul class="mt-3 flex flex-col gap-2 list-disc pl-5 text-ink">
              @for (line of recap()?.lines ?? []; track $index) { <li>{{ line }}</li> }
            </ul>
            <div class="mt-4 rounded-2xl bg-amber/80 text-ink p-4 font-display font-semibold">Remember: {{ recap()?.remember }}</div>
            <button type="button" (click)="startCheck('check')" class="mt-6 rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors">Quick check</button>
          </section>
        }

        @case ('check') {
          @let item = current();
          <section class="mt-6 rounded-2xl border border-cloud bg-white shadow-sm p-6">
            <p class="text-xs font-mono tracking-wider text-muted">{{ mode() === 'challenge' ? 'QUICK CHALLENGE' : 'QUICK CHECK' }} · {{ idx() }} OF {{ total() }}</p>
            @if (item) {
              <h2 class="font-display text-xl text-ink mt-1">{{ item.body }}</h2>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-4">
                @for (opt of item.options ?? []; track $index) {
                  <button type="button" [disabled]="picked() !== null" (click)="pick(opt)" [class]="checkOptClass(opt)">{{ opt }}</button>
                }
              </div>
              @if (picked() === null) {
                <button type="button" (click)="unsure()" class="mt-2 rounded-lg px-3 py-1.5 text-sm text-muted hover:bg-cloud/60 hover:text-ink transition-colors">Not sure</button>
              }

              @if (feedback(); as fb) {
                @if (fb.correct) {
                  <div class="mt-4 rounded-xl bg-moss/10 p-3 text-sm text-ink"><strong>Yes.</strong> {{ fb.reveal_answer }} is right.</div>
                } @else {
                  <div class="mt-4 rounded-xl bg-amber/20 p-3 text-sm text-ink">
                    <strong>{{ fb.unsure ? "That's fine." : 'Not quite.' }}</strong> {{ fb.hint }}
                    @if (sourceCard(fb.source_asset_id); as sc) {
                      <p class="mt-2 text-muted">Peek at "{{ sc.title }}": {{ sc.text }}</p>
                    }
                    <p class="mt-2">The answer is <strong>{{ fb.reveal_answer }}</strong>.</p>
                  </div>
                }
                <button type="button" (click)="nextQuestion()" class="mt-4 rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors">
                  {{ fb.done ? 'Finish' : 'Next question' }}
                </button>
              }
            }
          </section>
        }

        @case ('done') {
          <section class="mt-6 rounded-2xl border border-cloud bg-white shadow-sm p-6">
            <p class="text-xs font-mono tracking-wider text-moss-dark">ALL DONE</p>
            <h2 class="font-display text-2xl text-ink mt-1">You finished the session</h2>
            <p class="text-muted mt-2">{{ doneMessage() }}</p>
            <a [routerLink]="learnPath" class="inline-block mt-6 rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors">Back to Learn</a>
          </section>
        }
      }
    }
  `,
})
export default class CardSessionComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly learn = inject(LearnService);

  readonly learnPath = (this.route.snapshot.data['learnPath'] as string) ?? '/ramanujan/learn';
  private readonly conceptId = signal('');
  readonly loading = signal(true);
  readonly error = signal('');

  private readonly assets = signal<LearnAsset[]>([]);
  readonly cards = computed<CardData[]>(() =>
    this.assets()
      .filter((a) => a.kind === 'card')
      .sort((a, b) => a.order_index - b.order_index)
      .map((a) => a.data as CardData),
  );
  readonly recap = computed<RecapData | null>(
    () => (this.assets().find((a) => a.kind === 'recap')?.data as RecapData) ?? null,
  );
  private readonly cardAssets = computed(() => this.assets().filter((a) => a.kind === 'card').sort((a, b) => a.order_index - b.order_index));

  readonly step = signal<Step>('intro');
  readonly cardIx = signal(0);
  private readonly thinkPick = signal<Record<number, number>>({});
  private readonly thinkResults = signal<Record<number, ThinkResult>>({});

  readonly mode = signal<'check' | 'challenge'>('check');
  private readonly session = signal<CheckSession | null>(null);
  readonly current = signal<CheckItem | null>(null);
  readonly idx = signal(0);
  readonly total = signal(0);
  readonly picked = signal<string | null>(null);
  readonly feedback = signal<AnswerResult | null>(null);
  private skipEarned = false;

  readonly speaking = signal(false);

  async ngOnInit(): Promise<void> {
    const id = this.route.snapshot.paramMap.get('conceptId') ?? '';
    this.conceptId.set(id);
    try {
      this.assets.set(await this.learn.getAssets(id));
    } catch {
      this.error.set("Couldn't load this concept.");
    } finally {
      this.loading.set(false);
    }
  }

  ngOnDestroy(): void {
    this.stopAudio();
  }

  // --- trail ---
  readonly dots = computed(() => Array(this.cards().length + 2).fill(0));
  dotClass(i: number): string {
    const base = 'h-2.5 w-2.5 rounded-full';
    const pos = this.currentDot();
    if (i < pos) return `${base} bg-moss`;
    if (i === pos) return `${base} bg-white ring-2 ring-moss`;
    return `${base} border border-dashed border-muted`;
  }
  private currentDot(): number {
    const s = this.step();
    if (s === 'intro') return -1;
    if (s === 'card') return this.cardIx();
    if (s === 'recap') return this.cards().length;
    return this.cards().length + 1; // check / done
  }

  // --- cards + think-first ---
  startCards(): void {
    this.step.set('card');
    this.cardIx.set(0);
  }
  thinkAnswered(): boolean {
    return this.thinkPick()[this.cardIx()] !== undefined;
  }
  thinkLead(): string {
    const r = this.thinkResults()[this.cardIx()];
    return r === 'right' ? 'Yes.' : r === 'unsure' ? 'That is fine.' : 'Good try.';
  }
  pickThink(optionIndex: number): void {
    const ci = this.cardIx();
    const card = this.cards()[ci];
    const result: ThinkResult = optionIndex < 0 ? 'unsure' : optionIndex === card.think.answer_index ? 'right' : 'wrong';
    this.thinkPick.update((m) => ({ ...m, [ci]: optionIndex }));
    this.thinkResults.update((m) => ({ ...m, [ci]: result }));
  }
  thinkOptClass(i: number): string {
    const base = 'rounded-xl border px-4 py-2.5 text-sm text-left transition-colors';
    const picked = this.thinkPick()[this.cardIx()];
    const answer = this.cards()[this.cardIx()].think.answer_index;
    if (picked === undefined) return `${base} border-cloud bg-paper hover:border-moss text-ink`;
    if (i === answer) return `${base} border-moss bg-moss/10 text-ink`;
    if (i === picked) return `${base} border-amber bg-amber/10 text-ink`;
    return `${base} border-cloud bg-paper text-muted`;
  }
  nextCard(): void {
    this.stopAudio();
    if (this.cardIx() < this.cards().length - 1) {
      this.cardIx.update((i) => i + 1);
    } else {
      this.step.set('recap');
    }
  }

  // --- quick check (server-driven) ---
  async startCheck(mode: 'check' | 'challenge'): Promise<void> {
    this.stopAudio();
    this.mode.set(mode);
    const results = Object.values(this.thinkResults());
    const session = await this.learn.startCheck(this.conceptId(), results, mode);
    this.session.set(session);
    this.current.set(session.item);
    this.idx.set(session.index);
    this.total.set(session.total);
    this.picked.set(null);
    this.feedback.set(null);
    this.step.set('check');
  }
  checkOptClass(opt: string): string {
    const base = 'rounded-xl border px-4 py-2.5 text-sm text-left transition-colors';
    const fb = this.feedback();
    if (this.picked() === null) return `${base} border-cloud bg-paper hover:border-moss text-ink`;
    if (fb && opt === fb.reveal_answer) return `${base} border-moss bg-moss/10 text-ink`;
    if (opt === this.picked()) return `${base} border-amber bg-amber/10 text-ink`;
    return `${base} border-cloud bg-paper text-muted`;
  }
  async pick(choice: string): Promise<void> {
    if (this.picked() !== null) return;
    this.picked.set(choice);
    const result = await this.learn.answer(this.session()!.session_id, {
      item_id: this.current()!.id,
      choice,
    });
    this.feedback.set(result);
    if (result.skip_earned != null) this.skipEarned = result.skip_earned;
  }
  async unsure(): Promise<void> {
    if (this.picked() !== null) return;
    this.picked.set('__unsure__');
    const result = await this.learn.answer(this.session()!.session_id, {
      item_id: this.current()!.id,
      unsure: true,
    });
    this.feedback.set(result);
    if (result.skip_earned != null) this.skipEarned = result.skip_earned;
  }
  nextQuestion(): void {
    const fb = this.feedback();
    if (!fb) return;
    if (fb.done) {
      if (this.mode() === 'challenge' && !this.skipEarned) {
        // Didn't clear the skip — go through the cards together.
        this.mode.set('check');
        this.startCards();
      } else {
        this.step.set('done');
      }
      return;
    }
    this.current.set(fb.next_item);
    this.idx.set(fb.index + 1);
    this.picked.set(null);
    this.feedback.set(null);
  }

  sourceCard(assetId: string | null): CardData | null {
    if (!assetId) return null;
    const asset = this.cardAssets().find((a) => a.id === assetId);
    return (asset?.data as CardData) ?? null;
  }

  doneMessage(): string {
    return this.mode() === 'challenge' && this.skipEarned
      ? 'You clearly know this one. Nice.'
      : "That's the cards and the questions. No score — what matters is the thinking.";
  }

  // --- audio (device voice stand-in until a real recording is wired) ---
  toggleAudio(text: string): void {
    if (this.speaking()) {
      this.stopAudio();
      return;
    }
    if (!('speechSynthesis' in window)) return;
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 0.95;
    u.onend = () => this.speaking.set(false);
    u.onerror = () => this.speaking.set(false);
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
    this.speaking.set(true);
  }
  private stopAudio(): void {
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    this.speaking.set(false);
  }
}
