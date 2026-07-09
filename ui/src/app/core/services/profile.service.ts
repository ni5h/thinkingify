import { Injectable, computed, inject } from '@angular/core';
import { StorageService } from './storage.service';
import { Profile } from '../models';

@Injectable({ providedIn: 'root' })
export class ProfileService {
  private readonly storage = inject(StorageService);

  readonly profile = computed(() => this.storage.state().profile);

  update(changes: Partial<Profile>): void {
    this.storage.update((state) => ({
      ...state,
      profile: { ...state.profile, ...changes },
    }));
  }
}
