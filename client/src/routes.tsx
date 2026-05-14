import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { lazy, Suspense, useEffect } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { PageLoader } from '@/components/PageLoader';
import { RouteError } from '@/components/RouteError';
import { AgriStrategyPanel } from '@/components/AgriStrategyPanel';

// Lazy load all pages
const IndexPage = lazy(() => import('@/pages/Index').then(m => ({ default: m.IndexPage })));
const WelcomePage = lazy(() => import('@/pages/Welcome').then(m => ({ default: m.WelcomePage })));
const TokenizationPage = lazy(() => import('@/pages/TokenizationPage').then(m => ({ default: m.TokenizationPage })));
const AnalyticsPage = lazy(() => import('@/pages/AnalyticsPage').then(m => ({ default: m.AnalyticsPage })));
const AuthPage = lazy(() => import('@/pages/AuthPage').then(m => ({ default: m.AuthPage })));
const ActuarialLabPage = lazy(() => import('@/pages/ActuarialLabPage').then(m => ({ default: m.ActuarialLabPage })));
const OraclePage = lazy(() => import('@/pages/OraclePage').then(m => ({ default: m.OraclePage })));
const AtlasPage = lazy(() => import('@/pages/AtlasPage'));
const DemoPage = lazy(() => import('@/pages/DemoPage').then(m => ({ default: m.DemoPage })));

function LandingPageRedirect() {
  useEffect(() => {
    window.location.replace('/landing.html');
  }, []);

  return <PageLoader />;
}

const router = createBrowserRouter([
  {
    path: "/",
    errorElement: <RouteError />,
    element: (
      <Suspense fallback={<PageLoader />}>
        <LandingPageRedirect />
      </Suspense>
    ),
  },
  {
    path: "/demo",
    errorElement: <RouteError />,
    element: (
      <Suspense fallback={<PageLoader />}>
        <DemoPage />
      </Suspense>
    ),
  },
  {
    path: "/welcome",
    errorElement: <RouteError />,
    element: (
      <Suspense fallback={<PageLoader />}>
        <WelcomePage />
      </Suspense>
    ),
  },
  {
    path: "/auth",
    errorElement: <RouteError />,
    element: (
      <Suspense fallback={<PageLoader />}>
        <AuthPage />
      </Suspense>
    ),
  },
  {
    path: "/agro",
    errorElement: <RouteError />,
    element: (
      <Suspense fallback={<PageLoader />}>
        <AgriStrategyPanel />
      </Suspense>
    ),
  },
  {
    path: "/dashboard",
    errorElement: <RouteError />,
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
    errorElement: <RouteError />,
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
    errorElement: <RouteError />,
    element: (
      <ProtectedRoute>
        <Suspense fallback={<PageLoader />}>
          <AnalyticsPage />
        </Suspense>
      </ProtectedRoute>
    ),
  },
  {
    path: "/actuarial-lab",
    errorElement: <RouteError />,
    element: (
      <ProtectedRoute>
        <Suspense fallback={<PageLoader />}>
          <ActuarialLabPage />
        </Suspense>
      </ProtectedRoute>
    ),
  },
  {
    path: "/oracle",
    errorElement: <RouteError />,
    element: (
      <ProtectedRoute>
        <Suspense fallback={<PageLoader />}>
          <OraclePage />
        </Suspense>
      </ProtectedRoute>
    ),
  },
  {
    path: "/atlas",
    errorElement: <RouteError />,
    element: (
      <ProtectedRoute>
        <Suspense fallback={<PageLoader />}>
          <AtlasPage />
        </Suspense>
      </ProtectedRoute>
    ),
  },
]);

export function AppRoutes() {
  return <RouterProvider router={router} />;
}
