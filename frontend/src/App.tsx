import { Navigate, Route, Routes } from 'react-router-dom';
import type { ReactElement } from 'react';

import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import { defaultRouteByRole, getSession } from './lib/auth';
import type { Role } from './types/api';
import AdminPage from './pages/AdminPage';
import AnalyticsPage from './pages/AnalyticsPage';
import ApprovalsPage from './pages/ApprovalsPage';
import Dashboard from './pages/Dashboard';
import DealWorkspacePage from './pages/DealWorkspacePage';
import LoginPage from './pages/LoginPage';
import Pricing from './pages/Pricing';
import ProfilePage from './pages/ProfilePage';
import Products from './pages/Products';
import SalesDashboardPage from './pages/SalesDashboardPage';
import UploadCenterPage from './pages/UploadCenterPage';

function RoleGate({ allowed, children }: { allowed: Role[]; children: ReactElement }) {
  const session = getSession();
  if (!session) {
    return <Navigate to="/login" replace />;
  }
  if (!allowed.includes(session.user.role)) {
    return <Navigate to={defaultRouteByRole(session.user.role)} replace />;
  }
  return children;
}

export default function App() {
  const session = getSession();
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedRoute allowedRoles={['sales', 'approver', 'executive', 'admin']} />}>
        <Route element={<Layout />}>
          <Route
            path="/"
            element={
              <Navigate to={session ? defaultRouteByRole(session.user.role) : '/login'} replace />
            }
          />

          <Route
            path="/sales"
            element={
              <RoleGate allowed={['sales', 'admin']}>
                <SalesDashboardPage />
              </RoleGate>
            }
          />
          <Route
            path="/sales/quotes/new"
            element={
              <RoleGate allowed={['sales', 'admin']}>
                <DealWorkspacePage />
              </RoleGate>
            }
          />
          <Route
            path="/sales/quotes/:id"
            element={
              <RoleGate allowed={['sales', 'admin']}>
                <DealWorkspacePage />
              </RoleGate>
            }
          />

          <Route
            path="/dashboard"
            element={
              <RoleGate allowed={['sales', 'admin', 'approver', 'executive']}>
                <Dashboard />
              </RoleGate>
            }
          />
          <Route
            path="/products"
            element={
              <RoleGate allowed={['sales', 'admin', 'approver', 'executive']}>
                <Products />
              </RoleGate>
            }
          />
          <Route
            path="/pricing"
            element={
              <RoleGate allowed={['sales', 'admin', 'approver']}>
                <Pricing />
              </RoleGate>
            }
          />
          <Route
            path="/upload-center"
            element={
              <RoleGate allowed={['sales', 'admin', 'approver', 'executive']}>
                <UploadCenterPage />
              </RoleGate>
            }
          />

          <Route
            path="/approvals"
            element={
              <RoleGate allowed={['approver', 'admin']}>
                <ApprovalsPage />
              </RoleGate>
            }
          />

          <Route
            path="/analytics"
            element={
              <RoleGate allowed={['executive', 'admin', 'approver']}>
                <AnalyticsPage />
              </RoleGate>
            }
          />

          <Route
            path="/admin"
            element={
              <RoleGate allowed={['admin']}>
                <AdminPage />
              </RoleGate>
            }
          />

          <Route
            path="/profile"
            element={
              <RoleGate allowed={['sales', 'approver', 'executive', 'admin']}>
                <ProfilePage />
              </RoleGate>
            }
          />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
