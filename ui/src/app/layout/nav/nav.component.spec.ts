import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { NavComponent } from './nav.component';
import { AuthService } from '../../core/services/auth.service';
import { UserProfileService } from '../../core/services/user-profile.service';
import { FeatureFlagService } from '../../core/services/feature-flag.service';

function createNav(pilotMode: boolean): NavComponent {
  TestBed.configureTestingModule({
    imports: [NavComponent],
    providers: [
      provideRouter([]),
      { provide: FeatureFlagService, useValue: { pilotMode } },
      { provide: AuthService, useValue: { isAuthenticated: signal(false) } },
      { provide: UserProfileService, useValue: { me: signal(null) } },
    ],
  });
  return TestBed.createComponent(NavComponent).componentInstance;
}

describe('NavComponent nav filtering', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('shows all 6 tabs when pilotMode is off', () => {
    const nav = createNav(false);
    const paths = nav.items.map((i) => i.path);
    expect(nav.items.length).toBe(6);
    expect(paths).toContain('/einstein');
    expect(paths).toContain('/progress');
  });

  it('hides Einstein and Progress (4 tabs) when pilotMode is on', () => {
    const nav = createNav(true);
    const paths = nav.items.map((i) => i.path);
    expect(nav.items.length).toBe(4);
    expect(paths).not.toContain('/einstein');
    expect(paths).not.toContain('/progress');
    expect(paths).toEqual(['/dashboard', '/rowling', '/ramanujan', '/sherlock']);
  });
});
