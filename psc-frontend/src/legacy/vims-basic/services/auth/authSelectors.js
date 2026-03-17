export const selectAccessToken = (state) => state.auth.accessToken;
export const selectIsAuthenticated = (state) =>
  Boolean(state.auth.accessToken);
export const selectUser = (state) => state.auth.user;
