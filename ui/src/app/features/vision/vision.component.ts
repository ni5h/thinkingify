import { Component } from '@angular/core';
import { VisionHeroComponent } from './sections/vision-hero.component';
import { VisionWhyAnswersComponent } from './sections/vision-why-answers.component';
import { VisionWhyThinkingComponent } from './sections/vision-why-thinking.component';
import { VisionPhilosophyComponent } from './sections/vision-philosophy.component';
import { VisionThinkpadIntroComponent } from './sections/vision-thinkpad-intro.component';
import { VisionInvitationComponent } from './sections/vision-invitation.component';

@Component({
  selector: 'app-vision',
  standalone: true,
  imports: [
    VisionHeroComponent,
    VisionWhyAnswersComponent,
    VisionWhyThinkingComponent,
    VisionPhilosophyComponent,
    VisionThinkpadIntroComponent,
    VisionInvitationComponent,
  ],
  template: `
    <app-vision-hero />
    <app-vision-why-answers />
    <app-vision-why-thinking />
    <app-vision-philosophy />
    <app-vision-thinkpad-intro />
    <app-vision-invitation />
  `,
})
export default class VisionComponent {}
