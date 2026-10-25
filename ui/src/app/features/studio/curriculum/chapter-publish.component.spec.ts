import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import ChapterPublishComponent from './chapter-publish.component';
import { CurriculumService } from '../../../core/services/curriculum.service';

function counts(partial: Partial<Record<string, number>>) {
  return { draft: 0, reviewed: 0, live: 0, retired: 0, ...partial };
}

const content = {
  concepts: [
    { concept_id: 'x', title: 'Animal Groups', order_index: 0, items: counts({ draft: 2 }), assets: counts({ draft: 3, live: 1 }) },
  ],
  item_totals: counts({ draft: 2 }),
  asset_totals: counts({ draft: 3, live: 1 }),
  publishable_count: 5,
  live_count: 1,
};

function mount(service: unknown) {
  TestBed.configureTestingModule({
    imports: [ChapterPublishComponent],
    providers: [
      provideRouter([]),
      { provide: CurriculumService, useValue: service },
      { provide: ActivatedRoute, useValue: { snapshot: { paramMap: new Map([['id', 'ch1']]) } } },
    ],
  });
  return TestBed.createComponent(ChapterPublishComponent);
}

describe('ChapterPublishComponent', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('shows the publishable count, live count, and per-concept breakdown', async () => {
    const svc = { chapters: () => [{ id: 'ch1', title: 'Animals' }], getChapterContent: async () => content };
    const fixture = mount(svc);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('Animals'); // chapter title
    expect(text).toContain('Publish 5 to live'); // primary button
    expect(text).toContain('Unpublish'); // live_count > 0
    expect(text).toContain('Animal Groups');
    expect(text).toContain('draft'); // pending badge text
  });

  it('calls publishChapter and reports what was published', async () => {
    let published = false;
    const svc = {
      chapters: () => [{ id: 'ch1', title: 'Animals' }],
      getChapterContent: async () => (published ? { ...content, publishable_count: 0, live_count: 6 } : content),
      publishChapter: async () => { published = true; return { items: 2, assets: 3 }; },
    };
    const fixture = mount(svc);
    fixture.detectChanges();
    await fixture.whenStable();
    await fixture.componentInstance.publish();
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('Published 3 cards and 2 questions.');
    // Nothing left to publish → primary button hidden/disabled path shows 0
    expect(text).toContain('Publish 0 to live');
  });
});
