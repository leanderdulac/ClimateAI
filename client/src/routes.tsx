import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { PageLoader } from '@/components/PageLoader';

// Lazy load all pages
const IndexPage = lazy(() => import('@/pages/Index').then(m => ({ default: m.IndexPage })));
const WelcomePage = lazy(() => import('@/pages/Welcome').then(m => ({ default: m.WelcomePage })));
const TokenizationPage = lazy(() => import('@/pages/TokenizationPage').then(m => ({ default: m.TokenizationPage })));
const AnalyticsPage = lazy(() => import('@/pages/AnalyticsPage').then(m => ({ default: m.AnalyticsPage })));
const AuthPage = lazy(() => import('@/pages/AuthPage').then(m => ({ default: m.AuthPage })));

const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <Suspense fallback={<PageLoader />}>
        <WelcomePage />
      </Suspense>
    ),
  },
  {
    path: "/welcome",
    element: (
      <Suspense fallback={<PageLoader />}>
        <WelcomePage />
      </Suspense>
    ),
  },
  {
    path: "/auth",
    element: (
      <Suspense fallback={<PageLoader />}>
        <AuthPage />
      </Suspense>
    ),
  },
  {
    path: "/dashboard",
    element: (
      <ProtectedRoute>
        <Suspense fallback={<PageLoader />}>
          <IndexPage />
        </Suspense>
      </ProtectedRoute>
    ),
  },
  {
    path: "/tokenization",
    element: (
      <ProtectedRoute>
        <Suspense fallback={<PageLoader />}>
          <TokenizationPage />
        </Suspense>
      </ProtectedRoute>
    ),
  },
  {
    path: "/analytics",
    element: (
      <ProtectedRoute>
        <Suspense fallback={<PageLoader />}>
          <AnalyticsPage />
        </Suspense>
      </ProtectedRoute>
    ),
  },
]);

import { LanguageProvider } from '@/contexts/LanguageContext';

export function AppRoutes() {
  return (
    <LanguageProvider>
      <RouterProvider router={router} />
    </LanguageProvider>
  );
}
