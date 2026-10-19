import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import LearnLandingComponent from './learn-landing.component';
import { LearnService } from '../../../core/services/learn.service';

const svc = {
  getSubjects: async () => [{ id: 'm', name: 'Maths', code: 'maths', grade: 4 }],
  getChapters: async () => [{ id: 'ch', subject_id: 'm', title: 'Big Numbers', order_index: 0 }],
  getConcepts: async () => [
    { id: 'c1', chapter_id: 'ch', title: 'Reading large numbers', order_index: 0, prerequisites: [] },
    { id: 'c2', chapter_id: 'ch', title: 'Place value', order_index: 1, prerequisites: ['c1'] },
  ],
  getProgress: async () => [
    { concept_id: 'c1', state: 'solid', available: true, mastered: true },
    { concept_id: 'c2', state: 'learning', available: false, mastered: false },
  ],
};

describe('LearnLandingComponent', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('links available concepts and shows locked ones as muted', async () => {
    TestBed.configureTestingModule({
      imports: [LearnLandingComponent],
      providers: [provideRouter([]), { provide: LearnService, useValue: svc }],
    });
    const fixture = TestBed.createComponent(LearnLandingComponent);
    await fixture.componentInstance.ngOnInit();
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('Big Numbers');
    expect(text).toContain('Reading large numbers');
    expect(text).toContain('Finish earlier ones first'); // c2 is locked

    const link = fixture.nativeElement.querySelector('a[href="/ramanujan/learn/c1"]');
    expect(link).toBeTruthy();
    // the locked concept is not a link
    expect(fixture.nativeElement.querySelector('a[href="/ramanujan/learn/c2"]')).toBeNull();
  });
});
