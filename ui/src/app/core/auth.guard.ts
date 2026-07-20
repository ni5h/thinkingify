import { inject } from '@angular/core';
import { CanActivateFn, Router, RouterStateSnapshot } from '@angular/router';
import { AuthService } from './services/auth.service';

export const authGuard: CanActivateFn = async (_route, state: RouterStateSnapshot) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  await authService.ready;
  return authService.isAuthenticated()
    ? true
    : router.createUrlTree(['/studio/login'], { queryParams: { returnUrl: state.url } });
};

export const noAuthGuard: CanActivateFn = async () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  await authService.ready;
  return authService.isAuthenticated() ? router.createUrlTree(['/studio']) : true;
};

// Same shape as authGuard, redirecting to the Sherlock/Rowling login page
// instead — used for /sherlock*/rowling* routes. No role check: sign-up is
// open and access control is ownership-based, not role-based.
export const sherlockAuthGuard: CanActivateFn = async (_route, state: RouterStateSnapshot) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  await authService.ready;
  return authService.isAuthenticated()
    ? true
    : router.createUrlTree(['/sherlock/login'], { queryParams: { returnUrl: state.url } });
};

export const noPuzzleAuthGuard: CanActivateFn = async () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  await authService.ready;
  return authService.isAuthenticated() ? router.createUrlTree(['/sherlock']) : true;
};
