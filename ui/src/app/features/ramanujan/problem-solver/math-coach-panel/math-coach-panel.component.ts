import { Component, ElementRef, Input, OnInit, effect, inject, signal, viewChild } from '@angular/core';
import { MathService } from '../../../../core/services/math.service';
import { MathCoachMessage } from '../../../../core/models/math';

/**
 * The Socratic maths coach's chat — a clone of the Rowling writing
 * companion's panel, keyed on a problem instead of a draft. Smart
 * (injects MathService directly); the parent only decides where to mount
 * it and passes problemId + a per-visit sessionId.
 */
@Component({
  selector: 'app-math-coach-panel',
  standalone: true,
  template: `
    <div class="rounded-2xl border border-cloud bg-white shadow-sm flex flex-col h-full overflow-hidden">
      <div class="px-4 py-3 border-b border-cloud">
        <span class="text-sm font-medium text-ink">Thinking coach</span>
      </div>

      <div #scrollEl class="flex-1 overflow-y-auto p-4 flex flex-col gap-3 min-h-0">
        @if (messages().length === 0 && !sending()) {
          <p class="text-sm text-muted">
            Stuck, or want to think out loud? Tell me what you notice &mdash; I won't give you the
            answer, but I'll help you find it.
          </p>
        }
        @for (message of messages(); track message.id) {
          <div [class]="bubbleClass(message.role)">{{ message.body }}</div>
        }
        @if (sending()) {
          <div class="self-start max-w-[85%] rounded-2xl bg-cloud/60 text-muted px-3 py-2 text-sm italic">
            Thinking&hellip;
          </div>
        }
        @if (loadError()) {
          <p class="text-amber text-sm">{{ loadError() }}</p>
        }
      </div>

      <div class="flex gap-2 p-3 border-t border-cloud">
        <input
          type="text"
          [value]="draftInput()"
          (input)="draftInput.set($any($event.target).value)"
          (keydown.enter)="send()"
          placeholder="What are you thinking?"
          [disabled]="sending()"
          class="flex-1 min-w-0 rounded-xl border border-cloud bg-paper px-3 py-2 text-sm focus:outline-none focus:border-moss focus:ring-1 focus:ring-moss/30 transition-colors"
        />
        <button
          type="button"
          (click)="send()"
          [disabled]="sending() || !draftInput().trim()"
          class="rounded-xl bg-moss px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-moss-dark transition-colors disabled:opacity-60"
        >
          Send
        </button>
      </div>
    </div>
  `,
})
export class MathCoachPanelComponent implements OnInit {
  @Input({ required: true }) problemId!: string;
  @Input({ required: true }) sessionId!: string;

  private readonly math = inject(MathService);
  private readonly scrollEl = viewChild<ElementRef<HTMLElement>>('scrollEl');

  readonly messages = signal<MathCoachMessage[]>([]);
  readonly sending = signal(false);
  readonly draftInput = signal('');
  readonly loadError = signal<string | null>(null);

  constructor() {
    effect(() => {
      this.messages();
      this.sending();
      const el = this.scrollEl()?.nativeElement;
      if (el) queueMicrotask(() => (el.scrollTop = el.scrollHeight));
    });
  }

  async ngOnInit(): Promise<void> {
    try {
      this.messages.set(await this.math.listCoachMessages(this.problemId));
    } catch {
      this.loadError.set("Couldn't load your chat history. You can still send a new message.");
    }
  }

  bubbleClass(role: MathCoachMessage['role']): string {
    return role === 'user'
      ? 'self-end max-w-[85%] rounded-2xl bg-moss text-white px-3 py-2 text-sm'
      : 'self-start max-w-[85%] rounded-2xl bg-cloud/60 text-ink px-3 py-2 text-sm';
  }

  async send(): Promise<void> {
    const text = this.draftInput().trim();
    if (!text || this.sending()) return;

    const optimistic: MathCoachMessage = {
      id: crypto.randomUUID(),
      math_problem_id: this.problemId,
      role: 'user',
      body: text,
      ladder_level: null,
      asked_for_answer: false,
      answer_leak_blocked: false,
      is_fallback: false,
      created_at: new Date().toISOString(),
    };
    this.messages.update((list) => [...list, optimistic]);
    this.draftInput.set('');
    this.sending.set(true);
    this.loadError.set(null);

    try {
      const reply = await this.math.sendCoachMessage(this.problemId, text, this.sessionId);
      this.messages.update((list) => [...list, reply]);
    } catch {
      this.loadError.set("That message didn't send. Check your connection and try again.");
    } finally {
      this.sending.set(false);
    }
  }
}
