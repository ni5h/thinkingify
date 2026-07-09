import { environment } from '../../environments/environment';

export const APP_CONFIG = {
  apiBaseUrl: environment.apiBaseUrl,
  googleClientId: environment.googleClientId,
} as const;
