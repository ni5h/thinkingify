import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import CardSessionComponent from './card-session.component';
import { LearnService } from '../../../core/services/learn.service';

const CARDS = [
  {
    id: 'a1', concept_id: 'c', kind: 'card', url: null, order_index: 0,
    data: {
      title: 'Houses', text: 'Digits live in houses.', visual_brief: '', audio_script: 'think about it',
      think: { q: 'Which house?', options: ['Tens', 'Ones'], answer_index: 0, why: 'count from the right' },
    },
  },
  {
    id: 'a2', concept_id: 'c', kind: 'recap', url: null, order_index: 1,
    data: { lines: ['A digit worth depends on its house.'], remember: 'House decides worth.' },
  },
];

function fakeLearn(answerResult: unknown) {
  return {
    getAssets: async () => CARDS,
    startCheck: async () => ({
      session_id: 's1', index: 1, total: 2,
      item: { id: 'i1', concept_id: 'c', kind: 'recall', body: 'In 45 what is 4 worth?', options: ['40', '4'] },
      done: false,
    }),
    answer: async () => answerResult,
  };
}

function make(service: unknown) {
  TestBed.configureTestingModule({
    imports: [CardSessionComponent],
    providers: [
      provideRouter([]),
      { provide: LearnService, useValue: service },
      { provide: ActivatedRoute, useValue: { snapshot: { paramMap: new Map([['conceptId', 'c']]) } } },
    ],
  });
  return TestBed.createComponent(CardSessionComponent);
}

describe('CardSessionComponent', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('renders cards after loading', async () => {
    const fixture = make(fakeLearn({}));
    await fixture.componentInstance.ngOnInit();
    fixture.componentInstance.startCards();
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('Houses');
    expect(text).toContain('Digits live in houses.');
  });

  it('wrong answer shows a hint and the source card, never a score or level', async () => {
    const wrong = {
      correct: false, unsure: false, reveal_answer: '40', hint: 'The 4 lives in the Tens house.',
      source_asset_id: 'a1', index: 1, total: 2, done: false, next_item: null,
    };
    const fixture = make(fakeLearn(wrong));
    const c = fixture.componentInstance;
    await c.ngOnInit();
    await c.startCheck('check');
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('In 45 what is 4 worth?');

    await c.pick('4');
    fixture.detectChanges();
    const text = (fixture.nativeElement.textContent as string);
    expect(c.feedback()!.correct).toBe(false);
    expect(text).toContain('The 4 lives in the Tens house.'); // hint
    expect(text).toContain('Houses'); // source-card peek
    expect(text.toLowerCase()).not.toContain('score');
    expect(text).not.toMatch(/level\s*\d/i);
  });
});
