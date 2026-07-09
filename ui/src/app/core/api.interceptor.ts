import { HttpErrorResponse, HttpHandlerFn, HttpInterceptorFn, HttpRequest } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, from, switchMap, throwError } from 'rxjs';
import { AuthService } from './services/auth.service';
import { APP_CONFIG } from './config';

export const apiInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);

  const withBaseUrl = req.url.startsWith('http')
    ? req
    : req.clone({ url: `${APP_CONFIG.apiBaseUrl}${req.url}` });

  const token = authService.getAccessToken();
  const withAuth = token
    ? withBaseUrl.clone({ headers: withBaseUrl.headers.set('Authorization', `Bearer ${token}`) })
    : withBaseUrl;

  return next(withAuth).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401 && !req.url.includes('/auth/')) {
        return refreshAndRetry(authService, req, next);
      }
      return throwError(() => error);
    })
  );
};

function refreshAndRetry(authService: AuthService, req: HttpRequest<unknown>, next: HttpHandlerFn) {
  return from(authService.refreshToken()).pipe(
    switchMap((refreshed) => {
      if (!refreshed) {
        return throwError(() => new Error('Session expired'));
      }
      const newToken = authService.getAccessToken();
      const retried = req.url.startsWith('http')
        ? req
        : req.clone({ url: `${APP_CONFIG.apiBaseUrl}${req.url}` });
      return next(retried.clone({ headers: retried.headers.set('Authorization', `Bearer ${newToken}`) }));
    })
  );
}
