import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { FeatureGate } from '@/components/FeatureGate';
import { PageLoader } from '@/components/PageLoader';
import { RouteError } from '@/components/RouteError';
// Lazy load all pages
const IndexPage = lazy(() => import('@/pages/Index').then(m => ({ default: m.IndexPage })));
const WelcomePage = lazy(() => import('@/pages/Welcome').then(m => ({ default: m.WelcomePage })));
const TokenizationPage = lazy(() => import('@/pages/TokenizationPage').then(m => ({ default: m.TokenizationPage })));
const AnalyticsPage = lazy(() => import('@/pages/AnalyticsPage').then(m => ({ default: m.AnalyticsPage })));
const AuthPage = lazy(() => import('@/pages/AuthPage').then(m => ({ default: m.AuthPage })));
const ForgotPasswordPage = lazy(() => import('@/pages/ForgotPasswordPage').then(m => ({ default: m.ForgotPasswordPage })));
const ActuarialLabPage = lazy(() => import('@/pages/ActuarialLabPage').then(m => ({ default: m.ActuarialLabPage })));
const OraclePage = lazy(() => import('@/pages/OraclePage').then(m => ({ default: m.OraclePage })));
const AtlasPage = lazy(() => import('@/pages/AtlasPage'));
const DemoPage = lazy(() => import('@/pages/DemoPage').then(m => ({ default: m.DemoPage })));
const AgriStrategyPanel = lazy(() =>
  import('@/components/AgriStrategyPanel').then(m => ({ default: m.AgriStrategyPanel }))
);

const router = createBrowserRouter([
  {
    path: "/",
    errorElement: <RouteError />,
    element: (
      <Suspense fallback={<PageLoader />}>
        <WelcomePage />
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
    path: "/forgot-password",
    errorElement: <RouteError />,
    element: (
      <Suspense fallback={<PageLoader />}>
        <ForgotPasswordPage />
      </Suspense>
    ),
  },
  {
    path: "/agro",
    errorElement: <RouteError />,
    element: (
      <ProtectedRoute>
        <Suspense fallback={<PageLoader />}>
          <AgriStrategyPanel />
        </Suspense>
      </ProtectedRoute>
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
        <FeatureGate feature="tokenization">
          <Suspense fallback={<PageLoader />}>
            <TokenizationPage />
          </Suspense>
        </FeatureGate>
      </ProtectedRoute>
    ),
  },
  {
    path: "/analytics",
    errorElement: <RouteError />,
    element: (
      <ProtectedRoute>
        <FeatureGate feature="analytics">
          <Suspense fallback={<PageLoader />}>
            <AnalyticsPage />
          </Suspense>
        </FeatureGate>
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
        <FeatureGate feature="tokenization">
          <Suspense fallback={<PageLoader />}>
            <OraclePage />
          </Suspense>
        </FeatureGate>
      </ProtectedRoute>
    ),
  },
  {
    path: "/atlas",
    errorElement: <RouteError />,
    element: (
      <ProtectedRoute>
        <FeatureGate feature="atlas">
          <Suspense fallback={<PageLoader />}>
            <AtlasPage />
          </Suspense>
        </FeatureGate>
      </ProtectedRoute>
    ),
  },
]);

export function AppRoutes() {
  return <RouterProvider router={router} />;
}
