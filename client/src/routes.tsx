import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { IndexPage } from '@/pages/Index';
import { WelcomePage } from '@/pages/Welcome';

const router = createBrowserRouter([
  {
    path: "/",
    element: <WelcomePage />,
  },
  {
    path: "/welcome",
    element: <WelcomePage />,
  },
  {
    path: "/dashboard",
    element: <IndexPage />,
  },
  {
    path: "/admin",
    element: <div>Admin Panel</div>,
  },
]);

export function AppRoutes() {
  return <RouterProvider router={router} />;
}