import { AfterViewInit, Component, ElementRef, inject, signal, viewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { APP_CONFIG } from '../../../core/config';

@Component({
  selector: 'app-studio-login',
  standalone: true,
  template: `
    <div class="mx-auto mt-16 max-w-sm rounded-2xl border border-cloud bg-white shadow-sm p-8 text-center">
      <h1 class="font-display text-2xl text-ink">Thinkingify Studio</h1>
      <p class="text-muted text-sm mt-2">Sign in with an authorized Google account to write and manage posts.</p>

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
          class="rounded-xl border border-cloud bg-paper px-5 py-2.5 text-sm font-medium text-ink hover:border-moss hover:bg-cloud/60 transition-colors"
        >
          Continue as nish (dev)
        </button>
      </div>
    </div>
  `,
})
export default class StudioLoginComponent implements AfterViewInit {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  private readonly googleBtnContainer = viewChild<ElementRef<HTMLDivElement>>('googleBtn');
  private readonly returnUrl = this.route.snapshot.queryParamMap.get('returnUrl') ?? '/studio';

  readonly error = signal<string | null>(null);
  readonly googleUnavailable = signal(false);

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
    this.error.set(null);
    try {
      await this.authService.handleGoogleCredential(idToken);
      await this.router.navigateByUrl(this.returnUrl);
    } catch {
      this.error.set('Sign in failed — this Google account may not be authorized for Thinkingify Studio.');
    }
  }

  async handleDevLogin(): Promise<void> {
    this.error.set(null);
    try {
      await this.authService.devLogin();
      await this.router.navigateByUrl(this.returnUrl);
    } catch {
      this.error.set('Dev login is not enabled on this backend.');
    }
  }
}
