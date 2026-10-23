import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import EinsteinComponent from './einstein.component';
import { LearnService } from '../../core/services/learn.service';

const svc = {
  getSubjects: async () => [{ id: 'e', name: 'EVS', code: 'evs', grade: 4 }],
  getChapters: async () => [{ id: 'ch', subject_id: 'e', title: 'Animals', order_index: 0 }],
  getConcepts: async () => [
    { id: 'c1', chapter_id: 'ch', title: 'Animal Groups', order_index: 0, prerequisites: [] },
    { id: 'c2', chapter_id: 'ch', title: 'Animal Habitats', order_index: 1, prerequisites: ['c1'] },
    { id: 'c3', chapter_id: 'ch', title: 'Body Features', order_index: 2, prerequisites: ['c1', 'c2'] },
  ],
  getProgress: async () => [
    { concept_id: 'c1', state: 'solid', available: true, mastered: true },
    { concept_id: 'c2', state: 'learning', available: true, mastered: false },
    { concept_id: 'c3', state: 'learning', available: false, mastered: false },
  ],
};

describe('EinsteinComponent', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('renders the hero, chapter progress and the trail with done/now/locked states', async () => {
    TestBed.configureTestingModule({
      imports: [EinsteinComponent],
      providers: [provideRouter([]), { provide: LearnService, useValue: svc }],
    });
    const fixture = TestBed.createComponent(EinsteinComponent);
    await fixture.componentInstance.ngOnInit();
    fixture.detectChanges();

    const el = fixture.nativeElement;
    const text = el.textContent as string;
    expect(text).toContain('Einstein');
    expect(text).toContain('Animals');
    expect(text).toContain('1 of 3 explored'); // one concept solid

    // done (c1) and current (c2) are tappable; locked (c3) is not a link
    expect(el.querySelector('a[href="/einstein/learn/c1"]')).toBeTruthy();
    expect(el.querySelector('a[href="/einstein/learn/c2"]')).toBeTruthy();
    expect(el.querySelector('a[href="/einstein/learn/c3"]')).toBeNull();

    expect(text).toContain('Start →'); // the current node
    expect(text).toContain('Finish earlier ones first'); // the locked node
  });
});
