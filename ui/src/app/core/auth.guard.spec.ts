import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router, UrlTree } from '@angular/router';
import { adminGuard } from './auth.guard';
import { AuthService } from './services/auth.service';

function runAdminGuard(role: 'admin' | 'learner' | null): Promise<boolean | UrlTree> {
  TestBed.configureTestingModule({
    providers: [
      provideRouter([]),
      {
        provide: AuthService,
        useValue: { ready: Promise.resolve(), currentUser: signal(role ? { role } : null) },
      },
    ],
  });
  return TestBed.runInInjectionContext(() =>
    (adminGuard as (r: unknown, s: unknown) => Promise<boolean | UrlTree>)({}, {}),
  );
}

describe('adminGuard', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('allows admins through', async () => {
    expect(await runAdminGuard('admin')).toBe(true);
  });

  it('redirects a non-admin to /studio', async () => {
    const result = await runAdminGuard('learner');
    expect(result instanceof UrlTree).toBe(true);
    expect(TestBed.inject(Router).serializeUrl(result as UrlTree)).toBe('/studio');
  });

  it('redirects an anonymous visitor', async () => {
    expect((await runAdminGuard(null)) instanceof UrlTree).toBe(true);
  });
});
