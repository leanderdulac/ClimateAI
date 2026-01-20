/**
 * Protected Route Component
 * Wraps routes that require authentication
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';

interface ProtectedRouteProps {
    children: React.ReactNode;
    requireAuth?: boolean;
    requiredRole?: string | string[];
    redirectTo?: string;
}

/**
 * ProtectedRoute - Protects routes based on authentication status
 * 
 * @param children - The component to render if authorized
 * @param requireAuth - Whether authentication is required (default: true)
 * @param requiredRole - Optional role(s) required for access
 * @param redirectTo - Where to redirect if not authorized (default: /login)
 */
export function ProtectedRoute({
    children,
    requireAuth = true,
    requiredRole,
    redirectTo = '/login',
}: ProtectedRouteProps) {
    const { user, isLoading, isAuthenticated } = useAuth();
    const location = useLocation();

    // Show loading state
    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500"></div>
            </div>
        );
    }

    // Check authentication
    if (requireAuth && !isAuthenticated) {
        // Save the attempted URL for redirecting after login
        return <Navigate to={redirectTo} state={{ from: location }} replace />;
    }

    // Check role if required
    if (requiredRole && user) {
        const roles = Array.isArray(requiredRole) ? requiredRole : [requiredRole];
        if (!roles.includes(user.role || 'user')) {
            return <Navigate to="/unauthorized" replace />;
        }
    }

    return <>{children}</>;
}

/**
 * PublicRoute - For routes that should only be accessible when NOT authenticated
 * (e.g., login page should redirect to dashboard if already logged in)
 */
interface PublicRouteProps {
    children: React.ReactNode;
    redirectTo?: string;
}

export function PublicRoute({
    children,
    redirectTo = '/dashboard',
}: PublicRouteProps) {
    const { isLoading, isAuthenticated } = useAuth();
    const location = useLocation();

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500"></div>
            </div>
        );
    }

    // If authenticated, redirect to dashboard or where they came from
    if (isAuthenticated) {
        const from = (location.state as any)?.from?.pathname || redirectTo;
        return <Navigate to={from} replace />;
    }

    return <>{children}</>;
}

export default ProtectedRoute;
