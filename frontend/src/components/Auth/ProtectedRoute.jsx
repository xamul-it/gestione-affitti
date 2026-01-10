import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useTenant } from '../../contexts/TenantContext';

export default function ProtectedRoute({ children, requiredRole, requiredPermission, requireTenant = true }) {
  const { user, loading: authLoading, isAuthenticated, hasRole, hasPermission } = useAuth();
  const { hasTenant, loading: tenantLoading } = useTenant();
  const location = useLocation();

  // Combined loading state
  if (authLoading || tenantLoading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh'
      }}>
        <p>Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirect to login page, but save the location they were trying to access
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check tenant selection requirement
  if (requireTenant && !hasTenant) {
    // User is authenticated but hasn't selected a tenant yet
    return <Navigate to="/tenant-select" state={{ from: location }} replace />;
  }

  // Check role requirement
  if (requiredRole && !hasRole(requiredRole) && !user?.is_superuser) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <h2>Access Denied</h2>
        <p>You don't have permission to access this page.</p>
        <p>Required role: <strong>{requiredRole}</strong></p>
      </div>
    );
  }

  // Check permission requirement
  if (requiredPermission && !hasPermission(requiredPermission)) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <h2>Access Denied</h2>
        <p>You don't have permission to perform this action.</p>
        <p>Required permission: <strong>{requiredPermission}</strong></p>
      </div>
    );
  }

  return children;
}
