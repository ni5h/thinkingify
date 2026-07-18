export const environment = {
  production: true,
  apiBaseUrl: 'https://api.thinkingify.com',
  // Reusing sweet_pills' client for now, per user instruction — swap once a
  // dedicated Thinkingify OAuth client exists. https://thinkingify.com must
  // be on that client's "Authorized JavaScript origins" list in Google
  // Cloud Console for the sign-in button to render on the deployed site.
  googleClientId: '215968822427-sod1e3p8ddkl7jjdqchlphcfavgdig3g.apps.googleusercontent.com',
};
