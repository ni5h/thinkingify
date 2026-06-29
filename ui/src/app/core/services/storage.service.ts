import { Injectable, signal } from '@angular/core';
import { AppState, APP_STATE_VERSION, createEmptyAppState } from '../models';

const STORAGE_KEY = 'thinkingify:state';
const LEGACY_STORAGE_KEY = 'mental-models-gym:state';

/**
 * Single adapter over localStorage. No other service or component should
 * touch localStorage directly. State is held as a signal so that
 * ProgressService and feature services can derive computed() values that
 * stay in sync whenever any service writes through here.
 *
 * In V2 this becomes the only file that talks to a backend instead.
 */
@Injectable({ providedIn: 'root' })
export class StorageService {
  private readonly _state = signal<AppState>(this.readFromLocalStorage());

  readonly state = this._state.asReadonly();

  /** Replace the whole state and persist it. */
  save(state: AppState): void {
    this._state.set(state);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  /** Apply a partial update derived from the current state, then persist. */
  update(updater: (state: AppState) => AppState): void {
    this.save(updater(this._state()));
  }

  /** Marks today as an active day if it isn't already recorded. */
  recordActivityToday(): void {
    const today = new Date().toISOString().slice(0, 10);
    this.update((state) =>
      state.activityDates.includes(today)
        ? state
        : { ...state, activityDates: [...state.activityDates, today].sort() }
    );
  }

  exportState(): string {
    return JSON.stringify(this._state(), null, 2);
  }

  importState(json: string): void {
    this.save(this.migrate(JSON.parse(json) as AppState));
  }

  private readFromLocalStorage(): AppState {
    const raw = localStorage.getItem(STORAGE_KEY) ?? localStorage.getItem(LEGACY_STORAGE_KEY);
    if (!raw) {
      const empty = createEmptyAppState();
      localStorage.setItem(STORAGE_KEY, JSON.stringify(empty));
      return empty;
    }
    localStorage.removeItem(LEGACY_STORAGE_KEY);

    try {
      return this.migrate(JSON.parse(raw) as AppState);
    } catch {
      return createEmptyAppState();
    }
  }

  private migrate(state: AppState): AppState {
    if (!state.version || state.version < APP_STATE_VERSION) {
      return { ...createEmptyAppState(), ...state, version: APP_STATE_VERSION };
    }
    return state;
  }
}
