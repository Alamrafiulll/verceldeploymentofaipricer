import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { getSession, hasRole } from '../lib/auth';
import type { Role } from '../types/api';

interface Props {
  allowedRoles: Role[];
}

export default function ProtectedRoute({ allowedRoles }: Props) {
  const session = getSession();
  const location = useLocation();

  if (!session) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (!hasRole(session.user.role, allowedRoles)) {
    return <Navigate to={session.user.role === 'sales' ? '/sales' : '/login'} replace />;
  }

  return <Outlet />;
}
