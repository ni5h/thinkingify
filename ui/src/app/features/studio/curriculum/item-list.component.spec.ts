import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import ItemListComponent from './item-list.component';
import { CurriculumService, ItemFilter } from '../../../core/services/curriculum.service';

function makeComponent(filterSignal = signal<ItemFilter>({})) {
  const fakeService = {
    itemFilter: filterSignal,
    items: signal([]),
    concepts: signal([]),
    skills: signal([]),
    conceptsById: signal(new Map()),
  };
  TestBed.configureTestingModule({
    imports: [ItemListComponent],
    providers: [
      { provide: CurriculumService, useValue: fakeService },
      { provide: ActivatedRoute, useValue: { snapshot: { queryParamMap: new Map() } } },
    ],
  });
  const fixture = TestBed.createComponent(ItemListComponent);
  return { component: fixture.componentInstance, filter: filterSignal };
}

describe('ItemListComponent filtering', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('patches a single facet without clobbering the others', () => {
    const { component, filter } = makeComponent();
    component.setStatus('live');
    component.setKind('puzzle');
    expect(filter()).toEqual({ status: 'live', kind: 'puzzle' });
  });

  it('clears a facet when the empty option is chosen', () => {
    const { component, filter } = makeComponent(signal<ItemFilter>({ status: 'live', concept_id: 'c1' }));
    component.setStatus('');
    expect(filter().status).toBeUndefined();
    expect(filter().concept_id).toBe('c1');
  });
});
