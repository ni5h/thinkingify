import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import ParentDashboardComponent from './parent-dashboard.component';
import { ParentService } from '../../core/services/parent.service';

const overview = {
  child: { id: 'c1', name: 'Neo' },
  time_this_week_minutes: 42,
  solid_count: 2,
  total_concepts: 13,
  chapters: [
    {
      chapter_id: 'ch', subject: 'evs', title: 'Animals',
      concepts: [
        { concept_id: 'x', title: 'Animal Groups', state: 'solid', working_at: 'comfortable' },
        { concept_id: 'y', title: 'Animal Habitats', state: 'needs_look', working_at: 'stretching' },
      ],
    },
  ],
  recent: [{ concept_title: 'Animal Groups', when: '2026-10-23T10:00:00Z' }],
};

const svc = {
  getChildren: async () => [{ id: 'c1', name: 'Neo' }],
  getOverview: async () => overview,
  getDigest: async () => ({ lines: ['Neo has 2 of 13 concepts solid.', 'Worth another look together: Animal Habitats.'] }),
};

function mount(service: unknown) {
  TestBed.configureTestingModule({
    imports: [ParentDashboardComponent],
    providers: [provideRouter([]), { provide: ParentService, useValue: service }],
  });
  return TestBed.createComponent(ParentDashboardComponent);
}

describe('ParentDashboardComponent', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('shows the digest, time, and per-concept states — no ranks', async () => {
    const fixture = mount(svc);
    await fixture.componentInstance.ngOnInit();
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain("Neo's learning");
    expect(text).toContain('42'); // time this week
    expect(text).toContain('of 13'); // solid of total
    expect(text).toContain('Worth another look together: Animal Habitats.'); // digest
    expect(text).toContain('Solid'); // a solid concept
    expect(text).toContain('Another look'); // a needs_look concept
    expect(text.toLowerCase()).not.toContain('rank');
    expect(text.toLowerCase()).not.toContain('score');
  });

  it('shows a friendly empty state when no child is linked', async () => {
    const fixture = mount({ ...svc, getChildren: async () => [] });
    await fixture.componentInstance.ngOnInit();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain("Link your child");
  });
});
