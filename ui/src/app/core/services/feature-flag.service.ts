import { Injectable } from '@angular/core';
import { environment } from '../../../environments/environment';

/**
 * Small accessor for build-time feature flags so components and guards don't
 * each import `environment` directly. For the Class 4 pilot, `pilotMode` hides
 * unfinished rooms/modules and switches on the new look; toggling it off in the
 * environment files restores the pre-pilot behavior exactly.
 */
@Injectable({ providedIn: 'root' })
export class FeatureFlagService {
  readonly pilotMode = environment.pilotMode;
}
