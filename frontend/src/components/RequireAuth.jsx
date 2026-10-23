import { Navigate, useLocation } from 'react-router-dom';
import useAuth from '../hooks/useAuth';

/**
 * RequireAuth — protects routes that need an authenticated session.
 *
 * While the initial session check is in-flight the route renders nothing
 * (avoids flash of unauthenticated content).  Once the check completes,
 * unauthenticated users are redirected to /login.
 */
export default function RequireAuth({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    // Could render a spinner or skeleton here
    return null;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
