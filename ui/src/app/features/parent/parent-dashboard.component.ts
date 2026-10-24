import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import {
  ChildRef,
  ConceptState,
  ParentDigest,
  ParentOverview,
  ParentService,
} from '../../core/services/parent.service';

@Component({
  selector: 'app-parent-dashboard',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    <a routerLink="/profile" class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted hover:bg-cloud/60 hover:text-ink transition-colors">&larr; Profile</a>

    @if (loading()) {
      <p class="text-muted mt-6">Loading…</p>
    } @else if (children().length === 0) {
      <div class="mt-6 rounded-2xl border border-cloud bg-white shadow-sm p-6">
        <h1 class="font-display text-2xl text-ink">Parent dashboard</h1>
        <p class="text-muted mt-2">Link your child's account to see how their learning is going. You can do that from your <a routerLink="/profile" class="text-moss-dark hover:underline">profile</a>.</p>
      </div>
    } @else if (overview(); as ov) {
      <div class="flex items-baseline justify-between gap-4 mt-4">
        <h1 class="font-display text-2xl sm:text-3xl text-ink">{{ ov.child.name }}'s learning</h1>
        @if (children().length > 1) {
          <select class="rounded-xl border border-cloud bg-paper px-3 py-2 text-sm" (change)="selectChild($any($event.target).value)">
            @for (ch of children(); track ch.id) { <option [value]="ch.id" [selected]="ch.id === ov.child.id">{{ ch.name }}</option> }
          </select>
        }
      </div>

      <!-- Weekly digest -->
      @if (digest(); as d) {
        <div class="mt-4 rounded-2xl bg-ink text-white shadow-sm p-5">
          <p class="text-xs font-medium tracking-wider text-amber">THIS WEEK</p>
          <ul class="mt-2 flex flex-col gap-1.5">
            @for (line of d.lines; track $index) { <li class="text-[15px] leading-snug">{{ line }}</li> }
          </ul>
        </div>
      }

      <!-- Stats -->
      <div class="grid grid-cols-2 gap-4 mt-4">
        <div class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
          <p class="text-xs text-muted font-mono">Time this week</p>
          <p class="font-display text-3xl text-ink mt-1">{{ ov.time_this_week_minutes }}<span class="text-lg text-muted"> min</span></p>
        </div>
        <div class="rounded-2xl border border-cloud bg-white shadow-sm p-5">
          <p class="text-xs text-muted font-mono">Concepts solid</p>
          <p class="font-display text-3xl text-ink mt-1">{{ ov.solid_count }}<span class="text-lg text-muted"> of {{ ov.total_concepts }}</span></p>
        </div>
      </div>

      <!-- Chapters -->
      @for (chapter of ov.chapters; track chapter.chapter_id) {
        <h2 class="font-display text-lg mt-8">{{ chapter.title }}</h2>
        <div class="mt-3 flex flex-col gap-2">
          @for (c of chapter.concepts; track c.concept_id) {
            <div class="rounded-xl border border-cloud bg-white shadow-sm px-4 py-3 flex items-center justify-between gap-3">
              <span class="text-sm text-ink">{{ c.title }}</span>
              <div class="flex items-center gap-2 shrink-0">
                @if (c.working_at) { <span [class]="workClass(c.working_at)">{{ c.working_at }}</span> }
                <span [class]="stateClass(c.state)">{{ stateLabel(c.state) }}</span>
              </div>
            </div>
          }
        </div>
      }

      <!-- Recent -->
      @if (ov.recent.length) {
        <h2 class="font-display text-lg mt-8">Recently</h2>
        <ul class="mt-3 flex flex-col gap-1.5">
          @for (r of ov.recent; track $index) {
            <li class="text-sm text-muted">{{ r.concept_title }} <span class="text-xs">· {{ r.when | date: 'MMM d' }}</span></li>
          }
        </ul>
      }

      <p class="text-xs text-muted mt-8">Everything here is measured against {{ ov.child.name }}'s own progress — never other children. Mistakes are part of learning, not a mark against them.</p>
    }
  `,
})
export default class ParentDashboardComponent implements OnInit {
  private readonly parent = inject(ParentService);

  readonly loading = signal(true);
  readonly children = signal<ChildRef[]>([]);
  readonly overview = signal<ParentOverview | null>(null);
  readonly digest = signal<ParentDigest | null>(null);

  async ngOnInit(): Promise<void> {
    try {
      const children = await this.parent.getChildren();
      this.children.set(children);
      if (children.length > 0) {
        await this.load(children[0].id);
      }
    } finally {
      this.loading.set(false);
    }
  }

  async selectChild(childId: string): Promise<void> {
    await this.load(childId);
  }

  private async load(childId: string): Promise<void> {
    const [overview, digest] = await Promise.all([this.parent.getOverview(childId), this.parent.getDigest(childId)]);
    this.overview.set(overview);
    this.digest.set(digest);
  }

  stateLabel(state: ConceptState['state']): string {
    return state === 'solid' ? 'Solid' : state === 'needs_look' ? 'Another look' : 'In progress';
  }
  stateClass(state: ConceptState['state']): string {
    const base = 'rounded-lg px-2.5 py-0.5 text-xs font-medium';
    if (state === 'solid') return `${base} bg-moss/10 text-moss-dark`;
    if (state === 'needs_look') return `${base} bg-amber/20 text-ink`;
    return `${base} bg-cloud-soft text-muted`;
  }
  workClass(_work: NonNullable<ConceptState['working_at']>): string {
    return 'rounded-lg px-2.5 py-0.5 text-xs font-medium bg-room-einstein-tint text-room-einstein capitalize';
  }
}
