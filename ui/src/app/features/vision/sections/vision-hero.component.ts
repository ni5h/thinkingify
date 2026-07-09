import { Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { SketchComponent } from '../../../shared/components/sketch/sketch.component';
import { ProfileService } from '../../../core/services/profile.service';

@Component({
  selector: 'app-vision-hero',
  standalone: true,
  imports: [RouterLink, IconComponent, SketchComponent],
  template: `
    <section>
      <p class="font-mono text-xs uppercase tracking-widest text-muted">Thinkingify</p>

      <h1 class="font-display text-4xl sm:text-5xl md:text-6xl leading-[1.1] tracking-tight mt-4">
        <span class="text-muted block">The world teaches answers.</span>
        <span class="text-ink block mt-1">
          We teach
          <span class="relative inline-block">
            thinking
            <app-sketch name="circle-underline" [width]="150" [height]="110" class="text-navy absolute -left-3 -bottom-11 pointer-events-none" />
          </span>.
        </span>
      </h1>

      <p class="font-sans text-base text-muted max-w-md mt-6">{{ heroSubline() }}</p>
      <a routerLink="/profile" class="text-xs text-muted hover:text-ink transition-colors">edit</a>

      <div class="mt-10">
        <a routerLink="/journal" class="group inline-flex items-center gap-2 text-base font-medium text-moss">
          <span class="border-b border-moss/40 group-hover:border-moss pb-0.5 transition-colors">Start Thinking</span>
          <app-icon name="arrow-right" [size]="16" class="transition-transform group-hover:translate-x-0.5" />
        </a>
      </div>
    </section>
  `,
})
export class VisionHeroComponent {
  private readonly profileService = inject(ProfileService);
  private readonly profile = this.profileService.profile;

  readonly heroSubline = computed(() => {
    const { name, tagline } = this.profile();
    if (name && tagline) return `Built for ${name}, ${tagline}.`;
    if (name) return `Built for ${name}.`;
    if (tagline) return `Built for ${tagline}.`;
    return 'Built for one curious learner.';
  });
}
