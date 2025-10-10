import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { IndexPage } from '@/pages/Index';

const router = createBrowserRouter([
  {
    path: "/",
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