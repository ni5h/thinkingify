import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { lastValueFrom } from 'rxjs';

export type UserRole = 'admin' | 'author' | 'learner';

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: UserRole;
}

interface ApiUserOut {
  id: string;
  email: string;
  name: string;
  role: UserRole;
}

interface AuthTokens {
  access_token: string;
  refresh_token: string;
  user: ApiUserOut;
}

interface RefreshResponse {
  access_token: string;
}

/**
 * JWT-based auth against the FastAPI backend's /auth/google endpoint —
 * Google Identity Services on the client, a Studio-issued JWT (not Supabase
 * GoTrue) on the server. See api/app/services/auth_service.py.
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private static readonly ACCESS_TOKEN_KEY = 'thinkingify-studio:access_token';
  private static readonly REFRESH_TOKEN_KEY = 'thinkingify-studio:refresh_token';

  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  readonly currentUser = signal<AuthUser | null>(this.loadUserFromToken());
  readonly isAuthenticated = computed(() => this.currentUser() !== null);

  // Resolves once the initial auth state is actually settled. On a fresh
  // page load, loadUserFromToken() only ever checks the access token (30
  // min expiry) — if that's expired but a refresh token (7 day expiry)
  // still exists, this kicks off a silent refresh so guards don't bounce
  // an otherwise-valid session to the login screen. Guards await this
  // before reading isAuthenticated().
  readonly ready: Promise<void>;

  constructor() {
    if (this.currentUser() === null && localStorage.getItem(AuthService.REFRESH_TOKEN_KEY)) {
      this.ready = this.refreshToken().then(() => undefined);
    } else {
      this.ready = Promise.resolve();
    }
  }

  private loadUserFromToken(): AuthUser | null {
    const token = localStorage.getItem(AuthService.ACCESS_TOKEN_KEY);
    if (!token) return null;
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const payload = JSON.parse(
        decodeURIComponent(
          atob(base64)
            .split('')
            .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
            .join('')
        )
      ) as { sub: string; email: string; name: string; role: UserRole; exp: number };

      if (payload.exp * 1000 < Date.now()) return null;
      return { id: payload.sub, email: payload.email, name: payload.name, role: payload.role };
    } catch {
      return null;
    }
  }

  async handleGoogleCredential(idToken: string): Promise<void> {
    const tokens = await lastValueFrom(
      this.http.post<AuthTokens>('/api/v1/auth/google', { id_token: idToken })
    );
    this.storeTokens(tokens);
    this.currentUser.set(this.toAuthUser(tokens.user));
  }

  /** Fixed test identity, bypasses Google sign-in. 403s unless the backend
   * has ALLOW_DEV_LOGIN=true — see api/app/services/auth_service.py. */
  async devLogin(): Promise<void> {
    const tokens = await lastValueFrom(this.http.post<AuthTokens>('/api/v1/auth/dev-login', {}));
    this.storeTokens(tokens);
    this.currentUser.set(this.toAuthUser(tokens.user));
  }

  async refreshToken(): Promise<boolean> {
    const storedRefresh = localStorage.getItem(AuthService.REFRESH_TOKEN_KEY);
    if (!storedRefresh) return false;

    try {
      const response = await lastValueFrom(
        this.http.post<RefreshResponse>('/api/v1/auth/refresh', { refresh_token: storedRefresh })
      );
      localStorage.setItem(AuthService.ACCESS_TOKEN_KEY, response.access_token);
      this.currentUser.set(this.loadUserFromToken());
      return true;
    } catch {
      this.logout();
      return false;
    }
  }

  logout(): void {
    localStorage.removeItem(AuthService.ACCESS_TOKEN_KEY);
    localStorage.removeItem(AuthService.REFRESH_TOKEN_KEY);
    this.currentUser.set(null);
    // No more role-based "which section were they in" distinction — every
    // user can reach everything, so just send them to the neutral home page.
    void this.router.navigate(['/']);
  }

  getAccessToken(): string | null {
    return localStorage.getItem(AuthService.ACCESS_TOKEN_KEY);
  }

  private storeTokens(tokens: AuthTokens): void {
    localStorage.setItem(AuthService.ACCESS_TOKEN_KEY, tokens.access_token);
    localStorage.setItem(AuthService.REFRESH_TOKEN_KEY, tokens.refresh_token);
  }

  private toAuthUser(user: ApiUserOut): AuthUser {
    return { id: user.id, email: user.email, name: user.name, role: user.role };
  }
}
