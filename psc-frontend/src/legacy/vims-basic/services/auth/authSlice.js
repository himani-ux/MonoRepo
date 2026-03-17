import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  accessToken: null,
  refreshToken: null,
  user: null,
};

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    setCredentials: (state, action) => {
      const nextUser =
        action.payload.user !== undefined ? action.payload.user : state.user;

      state.accessToken = action.payload.accessToken;
      state.refreshToken = action.payload.refreshToken;
      state.user = nextUser;
    },

    logout: (state) => {
      state.accessToken = null;
      state.refreshToken = null;
      state.user = null;
    },
  },
});

export const { setCredentials, logout } = authSlice.actions;
export default authSlice.reducer;
