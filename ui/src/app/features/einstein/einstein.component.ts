import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ConceptProgress, LearnChapter, LearnConcept, LearnService } from '../../core/services/learn.service';

type NodeState = 'done' | 'now' | 'locked';
interface TrailNode extends LearnConcept {
  state: NodeState;
  side: 'l' | 'r';
}

@Component({
  selector: 'app-einstein',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="pb-4">
      <!-- Hero -->
      <div class="hero px-5 pt-5 pb-7 text-white">
        <a routerLink="/dashboard" class="relative z-10 inline-flex items-center gap-1.5 text-sm font-medium text-white/80 hover:text-white transition-colors">&larr; Rooms</a>
        <div class="relative z-10 flex items-center gap-3 mt-2">
          <svg class="w-11 h-11 shrink-0" viewBox="0 0 48 48" fill="none" stroke="#fff" stroke-width="1.8">
            <circle cx="24" cy="24" r="3.2" fill="#fff" stroke="none" />
            <ellipse cx="24" cy="24" rx="20" ry="8" />
            <ellipse cx="24" cy="24" rx="20" ry="8" transform="rotate(60 24 24)" />
            <ellipse cx="24" cy="24" rx="20" ry="8" transform="rotate(120 24 24)" />
            <circle cx="44" cy="24" r="2.2" fill="#F5C26B" stroke="none" />
            <circle cx="14" cy="41" r="2.2" fill="#9ED3C9" stroke="none" />
          </svg>
          <div>
            <h1 class="font-display text-2xl leading-tight">Einstein</h1>
            <p class="text-xs font-medium tracking-wider text-white/80 mt-0.5">SCIENCE &amp; EVS · CLASS 4</p>
          </div>
        </div>
        <p class="relative z-10 text-[15px] text-white/95 mt-3.5">Open your field notebook. Explore one idea at a time.</p>
      </div>

      @if (loading()) {
        <p class="text-muted mt-6">Loading…</p>
      } @else if (chapters().length === 0) {
        <div class="mt-6 rounded-2xl border border-cloud bg-white shadow-sm p-6">
          <p class="text-ink font-medium">Nothing here yet.</p>
          <p class="text-muted mt-1">Your chapters will appear once they're ready.</p>
        </div>
      } @else {
        <!-- Chapters -->
        <p class="text-xs font-bold tracking-widest text-muted mt-6 mb-2.5 px-1">CHAPTERS</p>
        <div class="flex gap-2.5 overflow-x-auto pb-1.5 -mx-1 px-1">
          @for (ch of chapters(); track ch.id; let first = $first) {
            <div [class]="first ? 'chip chip-active' : 'chip chip-soon'">
              <svg class="w-7 h-7 text-room-einstein" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
                <circle cx="8.5" cy="9" r="2" /><circle cx="15.5" cy="9" r="2" /><circle cx="6" cy="14" r="1.6" /><circle cx="18" cy="14" r="1.6" /><path d="M9 17c0-2 1.5-3 3-3s3 1 3 3-1.3 2.4-3 2.4S9 19 9 17Z" />
              </svg>
              <h3 class="font-display text-base mt-2">{{ ch.title }}</h3>
              @if (first) {
                <p class="text-xs text-muted">{{ solidCount() }} of {{ nodes().length }} explored</p>
                <div class="h-1.5 bg-room-einstein-tint rounded-full mt-2 overflow-hidden"><span class="block h-full bg-room-einstein rounded-full" [style.width.%]="progressPct()"></span></div>
              } @else {
                <p class="text-xs text-muted">Coming soon</p>
              }
            </div>
          }
          <div class="chip chip-soon flex flex-col items-center justify-center text-center">
            <p class="text-xs text-muted">More chapters<br />coming soon</p>
          </div>
        </div>

        <!-- Trail -->
        <p class="text-xs font-bold tracking-widest text-muted mt-6 mb-1 px-1 uppercase">{{ chapters()[0].title }} · Your trail</p>
        <div class="flex flex-col">
          @for (n of nodes(); track n.id; let i = $index) {
            <div class="stop" [class.side-l]="n.side === 'l'" [class.side-r]="n.side === 'r'">
              @if (i > 0) { <div class="conn"></div> }
              @if (n.state === 'locked') {
                <div class="node node-lock">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="5" y="11" width="14" height="9" rx="2" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></svg>
                </div>
              } @else {
                <a [routerLink]="['/einstein/learn', n.id]" [class]="n.state === 'done' ? 'node node-done' : 'node node-now'">
                  @if (n.state === 'now') { <span class="pin">Start</span> }
                  @if (n.state === 'done') {
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7" /></svg>
                  } @else {
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M12 3l2 5 5 .4-3.8 3.3 1.2 5-4.4-2.7-4.4 2.7 1.2-5L5 8.4 10 8z" /></svg>
                  }
                </a>
              }
              <div class="label">
                <div class="t" [class.text-muted]="n.state === 'locked'">{{ n.title }}</div>
                <div class="s" [class.go]="n.state === 'now'">{{ nodeSub(n.state) }}</div>
              </div>
            </div>
          }
        </div>
        <p class="text-center text-muted text-xs mt-5">Reach the end of the trail to finish the chapter.</p>
      }
    </div>
  `,
  styles: [`
    .hero{
      position:relative;overflow:hidden;border-radius:24px;
      background:linear-gradient(150deg,#2F5DA8,#1E3A6E);
    }
    .hero::before{
      content:"";position:absolute;inset:0;opacity:.5;
      background:radial-gradient(circle at 20% 30%, #fff 1px, transparent 0) 0 0/40px 40px,
                 radial-gradient(circle at 60% 70%, #fff 1px, transparent 0) 10px 12px/55px 55px;
    }
    .chip{flex:none;width:150px;background:#fff;border:1px solid #D5DCE6;border-radius:18px;padding:14px}
    .chip-active{border-color:#2F5DA8;box-shadow:0 2px 10px rgba(47,93,168,.12)}
    .chip-soon{opacity:.55}
    .stop{display:grid;grid-template-columns:1fr 60px 1fr;align-items:center}
    .conn{grid-column:2;justify-self:center;width:0;height:26px;border-left:2px dashed #AFC0DE}
    .node{grid-column:2;justify-self:center;width:54px;height:54px;border-radius:50%;display:flex;align-items:center;justify-content:center;position:relative;text-decoration:none}
    .node svg{width:24px;height:24px}
    .node-done{background:#2F5DA8;color:#fff;box-shadow:0 2px 8px rgba(47,93,168,.3)}
    .node-now{background:#fff;color:#2F5DA8;border:3px solid #2F5DA8;box-shadow:0 0 0 6px #E1EBF9}
    .node-lock{background:#EDF1F7;color:#9fb0c9;border:1px solid #D5DCE6}
    .pin{position:absolute;top:-9px;right:-10px;background:#F5C26B;color:#16213B;font-size:10px;font-weight:700;border-radius:999px;padding:2px 7px}
    .label{padding:6px 4px}
    .side-l .label{grid-column:1;text-align:right}
    .side-r .label{grid-column:3;text-align:left}
    .label .t{font-weight:600;font-size:14px;line-height:1.25;color:#16213B}
    .label .s{font-size:12px;color:#56627A;margin-top:1px}
    .label .s.go{color:#2F5DA8;font-weight:600}
  `],
})
export default class EinsteinComponent implements OnInit {
  private readonly learn = inject(LearnService);

  readonly loading = signal(true);
  readonly chapters = signal<LearnChapter[]>([]);
  readonly nodes = signal<TrailNode[]>([]);

  readonly solidCount = computed(() => this.nodes().filter((n) => n.state === 'done').length);
  readonly progressPct = computed(() => {
    const total = this.nodes().length;
    return total ? Math.round((this.solidCount() / total) * 100) : 0;
  });

  async ngOnInit(): Promise<void> {
    try {
      const subjects = await this.learn.getSubjects();
      const evs = subjects.find((s) => s.code === 'evs');
      if (!evs) return;
      const chapters = (await this.learn.getChapters(evs.id)).sort((a, b) => a.order_index - b.order_index);
      this.chapters.set(chapters);
      if (chapters.length === 0) return;

      const chapter = chapters[0];
      const [concepts, progress] = await Promise.all([
        this.learn.getConcepts(chapter.id),
        this.learn.getProgress(chapter.id),
      ]);
      const byId = new Map(progress.map((p) => [p.concept_id, p]));
      const ordered = concepts.sort((a, b) => a.order_index - b.order_index);
      this.nodes.set(ordered.map((c, i) => ({ ...c, state: this.stateOf(byId.get(c.id)), side: i % 2 ? 'l' : 'r' })));
    } finally {
      this.loading.set(false);
    }
  }

  private stateOf(p: ConceptProgress | undefined): NodeState {
    if (p?.state === 'solid') return 'done';
    if (p?.available ?? true) return 'now';
    return 'locked';
  }

  nodeSub(state: NodeState): string {
    return state === 'done' ? 'Done ✓' : state === 'now' ? 'Start →' : 'Finish earlier ones first';
  }
}
