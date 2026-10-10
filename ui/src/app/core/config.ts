import { environment } from '../../environments/environment';

export const APP_CONFIG = {
  apiBaseUrl: environment.apiBaseUrl,
  googleClientId: environment.googleClientId,
  pilotMode: environment.pilotMode,
} as const;
