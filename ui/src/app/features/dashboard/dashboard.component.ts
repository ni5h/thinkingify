import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { UserProfileService } from '../../core/services/user-profile.service';
import { HomeService, ContinueCard, selectConceptContinue } from '../../core/services/home.service';
import { FeatureFlagService } from '../../core/services/feature-flag.service';
import { LearnService } from '../../core/services/learn.service';
import { StepState } from '../../core/services/home.service';

interface RoomCard {
  name: string;
  subject: string;
  blurb: string;
  route: string;
  color: string;
  pilot: boolean;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [RouterLink],
  template: `
    <!-- Header: wordmark + child chip -->
    <div class="flex items-center justify-between gap-4">
      <a routerLink="/" class="font-display text-xl text-ink hover:text-moss transition-colors">Thinkingify</a>
      <div class="flex items-center gap-2.5">
        <span class="h-9 w-9 rounded-full bg-moss/10 text-moss-dark flex items-center justify-center font-display text-sm">{{ initial() }}</span>
        <div class="leading-tight">
          <p class="text-sm font-medium text-ink">{{ name() }}</p>
          <p class="text-xs text-muted">Class 4</p>
        </div>
      </div>
    </div>

    <h1 class="font-display text-2xl sm:text-3xl mt-8">Hi {{ name() }}. Ready to think?</h1>

    <!-- Row 1: Today's chapter + Crack it -->
    <div class="flex flex-col lg:flex-row gap-4 mt-6">
      <section class="lg:flex-[1.7] rounded-2xl border border-cloud bg-white shadow-sm p-6">
        <p class="text-xs font-medium tracking-wider text-muted">TODAY'S CHAPTER</p>
        <h2 class="font-display text-xl text-ink mt-1.5">{{ cont().title }}</h2>
        <p class="text-sm text-muted mt-1">{{ cont().subtitle }}</p>

        <div class="flex items-center mt-5" role="img" aria-label="Progress trail">
          @for (step of cont().steps; track $index; let last = $last) {
            <span [class]="dotClass(step.state)">
              @if (step.state === 'done') { <span class="text-[11px] leading-none">&check;</span> }
            </span>
            @if (!last) {
              <span class="h-0.5 flex-1" [style.background]="step.state === 'done' ? '#14746F' : '#D5DCE6'"></span>
            }
          }
        </div>

        <div class="flex flex-wrap gap-3 mt-6">
          <a [routerLink]="cont().route" class="rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors">
            Continue
          </a>
          <a routerLink="/ramanujan" class="rounded-xl border border-cloud bg-paper px-5 py-2.5 text-sm font-medium text-ink hover:border-moss transition-colors">
            Explore rooms
          </a>
        </div>
      </section>

      <section class="lg:flex-1 rounded-2xl bg-ink text-white shadow-sm p-6 flex flex-col">
        <p class="text-xs font-medium tracking-wider text-amber">CRACK IT</p>
        <p class="font-display text-lg mt-1.5">One puzzle</p>
        <p class="text-sm text-white/75 mt-2 flex-1">{{ crack().prompt }}</p>
        <p class="text-xs text-white/50 mt-4">No timer. No rank. Tell us how you know.</p>
        <a [routerLink]="crack().route" class="self-start mt-4 rounded-xl bg-amber px-5 py-2.5 text-sm font-medium text-ink hover:brightness-95 transition-all">
          Try it
        </a>
      </section>
    </div>

    <!-- Row 2: Rooms -->
    <h2 class="font-display text-xl mt-10">Rooms</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
      @for (room of rooms(); track room.route) {
        <a [routerLink]="room.route" class="rounded-2xl border border-cloud bg-white shadow-sm overflow-hidden hover:shadow-md transition-shadow">
          <div class="h-1.5" [style.background]="room.color"></div>
          <div class="p-5">
            <h3 class="font-display text-lg text-ink">{{ room.name }}</h3>
            <p class="text-sm font-medium mt-0.5" [style.color]="room.color">{{ room.subject }}</p>
            <p class="text-sm text-muted mt-2">{{ room.blurb }}</p>
          </div>
        </a>
      }
    </div>
  `,
})
export default class DashboardComponent implements OnInit {
  private readonly userProfile = inject(UserProfileService);
  private readonly home = inject(HomeService);
  private readonly flags = inject(FeatureFlagService);
  private readonly learn = inject(LearnService);

  readonly name = computed(() => this.userProfile.me()?.first_name || 'there');
  readonly initial = computed(() => (this.name().charAt(0) || '?').toUpperCase());
  // Prefer real concept progress (Phase 3) when the chapter has live content;
  // otherwise fall back to the cross-room "continue where you left off" card.
  private readonly conceptCont = signal<ContinueCard | null>(null);
  readonly cont = computed(() => this.conceptCont() ?? this.home.continueCard());

  async ngOnInit(): Promise<void> {
    try {
      const subjects = await this.learn.getSubjects();
      const maths = subjects.find((s) => s.code === 'maths');
      if (!maths) return;
      const chapters = await this.learn.getChapters(maths.id);
      if (chapters.length === 0) return;
      const chapter = [...chapters].sort((a, b) => a.order_index - b.order_index)[0];
      const [concepts, progress] = await Promise.all([
        this.learn.getConcepts(chapter.id),
        this.learn.getProgress(chapter.id),
      ]);
      this.conceptCont.set(selectConceptContinue(chapter.title, concepts, progress));
    } catch {
      // No live curriculum yet — keep the fallback card.
    }
  }
  readonly crack = this.home.crackIt;

  private readonly ALL_ROOMS: RoomCard[] = [
    { name: 'Ramanujan', subject: 'Maths', blurb: 'Learn each chapter, then crack olympiad-style puzzles.', route: '/ramanujan', color: '#14746F', pilot: true },
    { name: 'Rowling', subject: 'Writing', blurb: 'Explain ideas and tell stories in your own words.', route: '/rowling', color: '#7B3F86', pilot: true },
    { name: 'Sherlock Holmes', subject: 'Puzzles', blurb: 'Warm-up puzzles that sharpen your reasoning.', route: '/sherlock', color: '#94590C', pilot: true },
    { name: 'Einstein', subject: 'Science & EVS', blurb: 'Learn each chapter with cards, pictures and questions.', route: '/einstein', color: '#2F5DA8', pilot: true },
  ];

  // Only rooms that exist for the current mode (Einstein is hidden in the pilot).
  readonly rooms = computed(() =>
    this.flags.pilotMode ? this.ALL_ROOMS.filter((r) => r.pilot) : this.ALL_ROOMS,
  );

  dotClass(state: StepState): string {
    const base = 'h-6 w-6 rounded-full flex items-center justify-center shrink-0';
    if (state === 'done') return `${base} bg-moss text-white`;
    if (state === 'current') return `${base} border-2 border-moss bg-white`;
    return `${base} border-2 border-dashed border-cloud bg-white`;
  }
}
