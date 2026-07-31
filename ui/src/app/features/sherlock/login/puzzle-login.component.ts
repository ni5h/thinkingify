import { AfterViewInit, Component, ElementRef, inject, signal, viewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { APP_CONFIG } from '../../../core/config';

@Component({
  selector: 'app-puzzle-login',
  standalone: true,
  template: `
    <div class="mx-auto mt-16 max-w-sm rounded-2xl border border-cloud bg-white shadow-sm p-8 text-center relative">
      <h1 class="font-display text-2xl text-ink">Sherlock Holmes</h1>
      <p class="text-muted text-sm mt-2">Sign in to play your puzzles and save your progress.</p>

      <div class="mt-6 flex justify-center" #googleBtn></div>

      @if (googleUnavailable()) {
        <p class="text-amber text-sm mt-4">Google Sign-In couldn't load. Check your connection and reload.</p>
      }

      @if (error()) {
        <p class="text-amber text-sm mt-4">{{ error() }}</p>
      }

      <div class="mt-6 pt-6 border-t border-cloud">
        <button
          type="button"
          (click)="handleDevLogin()"
          [disabled]="signingIn()"
          class="rounded-xl border border-cloud bg-paper px-5 py-2.5 text-sm font-medium text-ink hover:border-moss hover:bg-cloud/60 transition-colors disabled:opacity-60"
        >
          Continue as nish (dev)
        </button>
      </div>

      @if (signingIn()) {
        <div class="absolute inset-0 rounded-2xl bg-white/90 flex items-center justify-center p-8">
          <p class="text-sm font-medium text-muted">Signing in&hellip; this can take a moment if the server's waking up.</p>
        </div>
      }
    </div>
  `,
})
export default class PuzzleLoginComponent implements AfterViewInit {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  private readonly googleBtnContainer = viewChild<ElementRef<HTMLDivElement>>('googleBtn');
  private readonly returnUrl = this.route.snapshot.queryParamMap.get('returnUrl') ?? '/sherlock';

  readonly error = signal<string | null>(null);
  readonly googleUnavailable = signal(false);
  readonly signingIn = signal(false);

  ngAfterViewInit(): void {
    this.initGoogleSignIn();
  }

  private initGoogleSignIn(): void {
    if (!window.google?.accounts?.id) {
      this.googleUnavailable.set(true);
      return;
    }

    window.google.accounts.id.initialize({
      client_id: APP_CONFIG.googleClientId,
      cancel_on_tap_outside: false,
      callback: (response) => {
        void this.handleCredential(response.credential);
      },
    });

    const container = this.googleBtnContainer()?.nativeElement;
    if (container) {
      window.google.accounts.id.renderButton(container, {
        type: 'standard',
        size: 'large',
        theme: 'outline',
        text: 'continue_with',
        shape: 'rectangular',
        width: 320,
      });
    }
  }

  private async handleCredential(idToken: string): Promise<void> {
    // Guards against an impatient double-click firing a second sign-in
    // while the first is still in flight (e.g. while the backend is
    // cold-starting) — without this, Google's button has no disabled
    // state of its own and happily fires a second concurrent request.
    if (this.signingIn()) return;
    this.signingIn.set(true);
    this.error.set(null);
    try {
      await this.authService.handleGoogleCredential(idToken);
      await this.router.navigateByUrl(this.returnUrl);
    } catch {
      this.error.set('Sign in failed — this Google account may not be authorized.');
    } finally {
      this.signingIn.set(false);
    }
  }

  async handleDevLogin(): Promise<void> {
    if (this.signingIn()) return;
    this.signingIn.set(true);
    this.error.set(null);
    try {
      await this.authService.devLogin();
      await this.router.navigateByUrl(this.returnUrl);
    } catch {
      this.error.set('Dev login is not enabled on this backend.');
    } finally {
      this.signingIn.set(false);
    }
  }
}
