import { TestBed } from '@angular/core/testing';
import { FeatureFlagService } from './feature-flag.service';
import { environment } from '../../../environments/environment';

describe('FeatureFlagService', () => {
  it('exposes the build-time pilotMode flag', () => {
    const service = TestBed.inject(FeatureFlagService);
    expect(service.pilotMode).toBe(environment.pilotMode);
    expect(typeof service.pilotMode).toBe('boolean');
  });
});
