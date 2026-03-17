/**
 * Application entry point.
 *
 * Sets up:
 * - React StrictMode
 * - TanStack Query provider
 * - Global styles
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import { registerServiceWorker } from '@/lib/pwa/register-sw';
import './index.css';

// Create a client with default options
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Don't refetch on window focus by default
      refetchOnWindowFocus: false,
      // Retry once on failure
      retry: 1,
      // Consider data stale after 5 minutes by default
      staleTime: 5 * 60 * 1000,
    },
    mutations: {
      // Retry once on failure
      retry: 1,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
);

// Register service worker for PWA support (production only)
// Source: IMPLEMENTATION_PLAN.md Step 8.3
registerServiceWorker();
