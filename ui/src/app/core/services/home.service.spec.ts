import { selectConceptContinue, selectContinue, selectCrackIt } from './home.service';
import { ContentListItem } from '../models/content';
import { BrotherTierState } from '../models/brother';
import { GameStats } from '../models/puzzle';

function draft(id: string, updated_at: string, title = 'Draft'): ContentListItem {
  return {
    id, title, slug: id, summary: null, feature_image_url: null, status: 'draft',
    topic_id: null, style: null, diary_theme: null, entry_date: null,
    published_at: null, updated_at, author: null,
  };
}
function tier(tier_id: string, status: BrotherTierState['status']): BrotherTierState {
  return { tier_id, name: tier_id.toUpperCase(), status, baseline_ms: null, median_ms: null, accuracy: null, attempts_count: 0 };
}
function kak(op: string, last_attempt_at: string | null): GameStats {
  return { game_id: `kakooma-${op}`, current_tier: 'trial', total_attempts: 1, attempts_today: 0, attempts_this_week: 1, total_time_ms: 0, last_attempt_at };
}

describe('selectContinue', () => {
  it('picks the most recent of a draft vs Kakooma practice', () => {
    const olderDraft = draft('d1', '2026-10-01T10:00:00Z', 'My story');
    const newerKakooma = kak('add', '2026-10-05T10:00:00Z');
    const card = selectContinue([olderDraft], [], [newerKakooma]);
    expect(card.room).toBe('sherlock');
    expect(card.route).toEqual(['/sherlock/kakooma', 'add']);
  });

  it('picks the draft when it is the most recent', () => {
    const newerDraft = draft('d2', '2026-10-09T10:00:00Z', 'Newer');
    const olderKakooma = kak('add', '2026-10-02T10:00:00Z');
    const card = selectContinue([newerDraft], [], [olderKakooma]);
    expect(card.room).toBe('rowling');
    expect(card.title).toBe('Newer');
    expect(card.route).toEqual(['/rowling/write', 'd2']);
  });

  it('ignores diary drafts and published posts', () => {
    const diary = { ...draft('x', '2026-10-09T10:00:00Z'), style: 'diary_entry' };
    const published = { ...draft('y', '2026-10-09T10:00:00Z'), status: 'published' as const };
    const card = selectContinue([diary, published], [tier('b1', 'active')], []);
    expect(card.room).toBe('ramanujan'); // falls through to Brothers
  });

  it('falls back to the active Brothers tier', () => {
    const card = selectContinue([], [tier('b1', 'mastered'), tier('b2', 'active')], []);
    expect(card.room).toBe('ramanujan');
    expect(card.title).toContain('B2');
    expect(card.steps.filter((s) => s.state === 'done').length).toBe(1); // one mastered
    expect(card.route).toEqual(['/ramanujan/brothers']);
  });

  it('returns a sensible starter when there is no activity', () => {
    const card = selectContinue([], [], []);
    expect(card.room).toBe('ramanujan');
    expect(card.steps.length).toBe(5);
    expect(card.steps[0].state).toBe('current');
  });
});

describe('selectCrackIt', () => {
  it('picks an unattempted operation first', () => {
    const card = selectCrackIt([kak('add', '2026-10-05T10:00:00Z')]);
    // subtract/multiply/divide are unattempted (empty ts sorts first)
    expect(card.operation).not.toBe('add');
    expect(card.route[0]).toBe('/sherlock/kakooma');
  });

  it('picks the least-recently practiced when all attempted', () => {
    const stats = [
      kak('add', '2026-10-09T10:00:00Z'),
      kak('subtract', '2026-10-01T10:00:00Z'),
      kak('multiply', '2026-10-08T10:00:00Z'),
      kak('divide', '2026-10-07T10:00:00Z'),
    ];
    expect(selectCrackIt(stats).operation).toBe('subtract');
  });
});

describe('selectConceptContinue', () => {
  const concepts = [
    { id: 'c1', title: 'Reading large numbers', order_index: 0 },
    { id: 'c2', title: 'Place value', order_index: 1 },
    { id: 'c3', title: 'Comparing', order_index: 2 },
  ];

  it('returns null when there is no chapter content', () => {
    expect(selectConceptContinue('Big Numbers', [], [])).toBeNull();
  });

  it('points at the first available concept that is not yet solid', () => {
    const progress = [
      { concept_id: 'c1', state: 'solid', available: true },
      { concept_id: 'c2', state: 'learning', available: true },
      { concept_id: 'c3', state: 'learning', available: false },
    ];
    const card = selectConceptContinue('Big Numbers', concepts, progress)!;
    expect(card.room).toBe('ramanujan');
    expect(card.title).toBe('Place value');
    expect(card.route).toEqual(['/ramanujan/learn', 'c2']);
    expect(card.subtitle).toBe('Big Numbers');
    // trail reflects how many concepts are solid
    expect(card.steps.filter((s) => s.state === 'done').length).toBe(1);
  });

  it('skips locked concepts', () => {
    const progress = [
      { concept_id: 'c1', state: 'solid', available: true },
      { concept_id: 'c2', state: 'solid', available: true },
      { concept_id: 'c3', state: 'learning', available: false },
    ];
    // c3 is the only non-solid but it's locked → fall back to first available
    const card = selectConceptContinue('Big Numbers', concepts, progress)!;
    expect(card.title).toBe('Reading large numbers');
  });
});
