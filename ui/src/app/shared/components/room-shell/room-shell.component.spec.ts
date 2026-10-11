import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { RoomShellComponent, RoomDoor } from './room-shell.component';

const DOORS: RoomDoor[] = [
  { id: 'learn', title: 'Learn', blurb: 'Coach you through it.', route: '/x', recommended: true },
  { id: 'brothers', title: 'Brothers', blurb: 'Warm up.', route: '/y' },
];

function render(doors: RoomDoor[]): HTMLElement {
  TestBed.configureTestingModule({
    imports: [RoomShellComponent],
    providers: [provideRouter([])],
  });
  const fixture = TestBed.createComponent(RoomShellComponent);
  fixture.componentRef.setInput('roomName', 'Ramanujan');
  fixture.componentRef.setInput('subjectLabel', 'Maths');
  fixture.componentRef.setInput('tone', 'ramanujan');
  fixture.componentRef.setInput('icon', 'puzzle');
  fixture.componentRef.setInput('doors', doors);
  fixture.detectChanges();
  return fixture.nativeElement as HTMLElement;
}

describe('RoomShellComponent', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('renders exactly the doors it is given', () => {
    const el = render(DOORS);
    const doorEls = el.querySelectorAll('a[href]');
    expect(doorEls.length).toBe(2);
    expect(el.textContent).toContain('Learn');
    expect(el.textContent).toContain('Brothers');
  });

  it('renders no doors when none are provided (none exist yet)', () => {
    const el = render([]);
    expect(el.querySelectorAll('a[href]').length).toBe(0);
    expect(el.textContent).toContain('Ramanujan');
  });

  it('rings the recommended door with the tone color', () => {
    const el = render(DOORS);
    const doorEls = Array.from(el.querySelectorAll('a[href]')) as HTMLElement[];
    const learn = doorEls.find((a) => a.textContent?.includes('Learn'))!;
    const brothers = doorEls.find((a) => a.textContent?.includes('Brothers'))!;
    expect(learn.style.borderWidth).toBe('2px');
    // ramanujan tone #14746F -> rgb(20, 116, 111)
    expect(learn.style.borderColor).toBe('rgb(20, 116, 111)');
    expect(brothers.style.borderWidth).toBe('1px');
  });
});
