export const environment = {
  production: false,
  // Class 4 pilot: hides unfinished rooms/modules and applies the new look.
  // Toggle off to restore the pre-pilot behavior exactly.
  pilotMode: true,
  apiBaseUrl: 'http://localhost:8000',
  // Dedicated Thinkingify OAuth client (replaces the reused sweet_pills
  // one). http://localhost:4200 must be on this client's "Authorized
  // JavaScript origins" list in Google Cloud Console for the sign-in
  // button to render here.
  googleClientId: '631847061926-a9g9rplpf07k17rfeu4n24b0d5dajduc.apps.googleusercontent.com',
};
