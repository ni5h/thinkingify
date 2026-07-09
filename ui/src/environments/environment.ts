export const environment = {
  production: false,
  apiBaseUrl: 'http://localhost:8000',
  // Reusing sweet_pills' client for now, per user instruction — swap once a
  // dedicated Thinkingify OAuth client exists. http://localhost:4200 must be
  // on that client's "Authorized JavaScript origins" list in Google Cloud
  // Console for the sign-in button to render here.
  googleClientId: '215968822427-sod1e3p8ddkl7jjdqchlphcfavgdig3g.apps.googleusercontent.com',
};
