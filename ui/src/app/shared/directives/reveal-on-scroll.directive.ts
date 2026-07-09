import { AfterViewInit, Directive, ElementRef, OnDestroy, inject } from '@angular/core';

/**
 * One-shot scroll-triggered fade/rise for the vision page's long-form
 * sections. Distinct from the shell's slideUp (page-entry animation) — this
 * plays once per section as it's scrolled into view, never loops (the
 * IntersectionObserver unobserves itself after the first fire), and is
 * skipped entirely under prefers-reduced-motion.
 */
@Directive({
  selector: '[appRevealOnScroll]',
  standalone: true,
})
export class RevealOnScrollDirective implements AfterViewInit, OnDestroy {
  private readonly el = inject(ElementRef<HTMLElement>);
  private observer?: IntersectionObserver;

  ngAfterViewInit(): void {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion || typeof IntersectionObserver === 'undefined') {
      return;
    }

    const element = this.el.nativeElement;
    element.classList.add('opacity-0');

    this.observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            element.classList.remove('opacity-0');
            element.classList.add('animate-revealUp');
            this.observer?.unobserve(element);
          }
        }
      },
      { threshold: 0.15 }
    );
    this.observer.observe(element);
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
  }
}
