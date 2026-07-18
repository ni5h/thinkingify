import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService, UserRole } from './services/auth.service';

export const authGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return authService.isAuthenticated() ? true : router.createUrlTree(['/studio/login']);
};

export const noAuthGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return authService.isAuthenticated() ? router.createUrlTree(['/studio']) : true;
};

/**
 * Role-aware guard factory — plain isAuthenticated() checks (above) let any
 * logged-in role reach any guarded route (e.g. a learner could navigate to
 * /studio and see the shell render before every API call 403s). This closes
 * that gap: redirects to the right login page if logged out, or away from
 * the wrong section entirely if logged in as the wrong role.
 */
function roleGuard(loginPath: string, ...roles: UserRole[]): CanActivateFn {
  return () => {
    const authService = inject(AuthService);
    const router = inject(Router);
    const user = authService.currentUser();

    if (user && roles.includes(user.role)) return true;
    return router.createUrlTree([user ? '/' : loginPath]);
  };
}

export const requireStudioRole = roleGuard('/studio/login', 'admin', 'author');
export const requireLearnerRole = roleGuard('/sherlock/login', 'admin', 'learner');

export const noPuzzleAuthGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return authService.isAuthenticated() ? router.createUrlTree(['/sherlock']) : true;
};
