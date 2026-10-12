import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import CurriculumTreeComponent from './curriculum-tree.component';
import { CurriculumService } from '../../../core/services/curriculum.service';

function makeFixture() {
  const fakeService = {
    subjects: signal([{ id: 's1', name: 'Maths', code: 'maths' }]),
    chapters: signal([{ id: 'ch1', subject_id: 's1', title: 'Big Numbers', order_index: 0 }]),
    concepts: signal([{ id: 'co1', chapter_id: 'ch1', title: 'Place value', order_index: 0 }]),
  };
  TestBed.configureTestingModule({
    imports: [CurriculumTreeComponent],
    providers: [provideRouter([]), { provide: CurriculumService, useValue: fakeService }],
  });
  const fixture = TestBed.createComponent(CurriculumTreeComponent);
  fixture.detectChanges();
  return fixture;
}

describe('CurriculumTreeComponent', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('renders subjects and their chapters', () => {
    const text = makeFixture().nativeElement.textContent as string;
    expect(text).toContain('Maths');
    expect(text).toContain('Big Numbers');
  });

  it('reveals a chapter\'s concepts only after it is expanded', () => {
    const fixture = makeFixture();
    expect(fixture.nativeElement.textContent).not.toContain('Place value');

    fixture.componentInstance.toggle('ch1');
    fixture.detectChanges();
    expect(fixture.componentInstance.isOpen('ch1')).toBe(true);
    expect(fixture.nativeElement.textContent).toContain('Place value');
  });
});
