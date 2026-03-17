import { configureStore, combineReducers } from "@reduxjs/toolkit";
import { persistReducer, persistStore } from "redux-persist";
import storage from "redux-persist/lib/storage";

import authReducer from "../services/auth/authSlice";
import uiReducer from "./uiSlice";
import { authApi } from "../services/auth/authApi";
import { orbApi } from "../services/orb/orbApi";


const rootReducer = combineReducers({
  auth: authReducer,
  ui: uiReducer,
  [authApi.reducerPath]: authApi.reducer,
  [orbApi.reducerPath]: orbApi.reducer,
});

const persistConfig = {
  key: "legacy-vims-basic",
  storage,
  whitelist: ["ui"],
};

const store = configureStore({
  reducer: persistReducer(persistConfig, rootReducer),
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }).concat(authApi.middleware, orbApi.middleware),
});

export const persistor = persistStore(store);
export default store;
