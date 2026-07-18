export const environment = {
  production: true,
  apiBaseUrl: 'https://api.thinkingify.com',
  // Dedicated Thinkingify OAuth client (replaces the reused sweet_pills
  // one). https://thinkingify.com must be on this client's "Authorized
  // JavaScript origins" list in Google Cloud Console for the sign-in
  // button to render on the deployed site.
  googleClientId: '631847061926-a9g9rplpf07k17rfeu4n24b0d5dajduc.apps.googleusercontent.com',
};
