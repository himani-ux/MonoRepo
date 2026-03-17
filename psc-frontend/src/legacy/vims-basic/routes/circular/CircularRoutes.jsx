import React, { useEffect } from "react";
import { Routes, Route, Navigate, useNavigate } from "react-router-dom";

import MainDashboard from "../../pages/circular/MainDashboard";
import Dashboard from "../../pages/circular/Dashboard";
import Admin from "../../pages/circular/Officeuser";

import PdfViewerPage from "../../pages/circular/PdfViewerPage";
import RoleLanding from "../../pages/circular/RoleLanding";
import AdminAllNotifications from "../../pages/circular/AdminAllNotifications";
import UserNotifications from "../../pages/circular/UserNotifications";
import DraftNotifications from "../../pages/circular/DraftNotifications";
import ApprovedNotificationsLibrary from "../../pages/circular/ApprovedNotificationsLibrary";

import { useAuth } from "../../hooks/auth/useAuth";

/* ---------------- DEFAULT ROUTE ---------------- */
const DefaultRouteHandler = () => {
  const { user, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (loading) return;

    if (user?.user_type === "office") {
      navigate("dashboard", { replace: true });
    } else if (user?.user_type === "ship") {
      navigate("ship-dashboard", { replace: true });
    } else {
      navigate("role-landing", { replace: true });
    }
  }, [user, loading, navigate]);

  return null;
};

/* ---------------- ROLE GUARDS ---------------- */
const OfficeOnly = ({ children }) => {
  const { user } = useAuth();
  return user?.user_type === "office" ? (
    children
  ) : (
    <Navigate to="/circular" replace />
  );
};

const ShipOnly = ({ children }) => {
  const { user } = useAuth();
  return user?.user_type === "ship" ? (
    children
  ) : (
    <Navigate to="/circular" replace />
  );
};

const AdminOnly = ({ children }) => {
  const { user } = useAuth();

  const isAdmin =
    user?.user_type === "office" && user?.role_name?.toLowerCase() === "admin";

  return isAdmin ? children : <Navigate to="/circular/dashboard" replace />;
};

const UserNotificationsWrapper = () => {
  const { user, loading } = useAuth();

  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  if (user.user_type !== "office")
    return <Navigate to="/circular/dashboard" replace />;

  return <UserNotifications currentUser={user} />;
};

const DraftNotificationsWrapper = () => {
  const { user, loading } = useAuth();

  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  if (user.user_type !== "office")
    return <Navigate to="/circular/dashboard" replace />;

  return <DraftNotifications currentUser={user} />;
};

/* ---------------- ROUTES ---------------- */
function CircularRoutes() {
  return (
    <Routes>
      {/* Default entry → redirect by role */}
      <Route index element={<DefaultRouteHandler />} />

      {/* Public inside circular */}
      <Route path="role-landing" element={<RoleLanding />} />

      {/* Office */}
      <Route
        path="dashboard"
        element={
          <OfficeOnly>
            <MainDashboard />
          </OfficeOnly>
        }
      />

      <Route
        path="office"
        element={
          <OfficeOnly>
            <Admin />
          </OfficeOnly>
        }
      />

      {/* Admin */}
      <Route
        path="admin"
        element={
          <AdminOnly>
            <Admin />
          </AdminOnly>
        }
      />

      <Route
        path="admin/all-notifications"
        element={
          <AdminOnly>
            <AdminAllNotifications />
          </AdminOnly>
        }
      />

      {/* Office User */}
      <Route
        path="user/notifications"
        element={
          <OfficeOnly>
            <UserNotificationsWrapper />
          </OfficeOnly>
        }
      />

      <Route
        path="user/drafts"
        element={
          <OfficeOnly>
            <DraftNotificationsWrapper />
          </OfficeOnly>
        }
      />

      {/* Common */}
      <Route
        path="approved-library"
        element={<ApprovedNotificationsLibrary />}
      />

      {/* Ship */}
      <Route
        path="ship-dashboard"
        element={
          <ShipOnly>
            <Dashboard />
          </ShipOnly>
        }
      />

      {/* PDF */}
      <Route path="pdf-viewer" element={<PdfViewerPage />} />

      {/* Catch-all inside circular */}
      <Route path="*" element={<DefaultRouteHandler />} />
    </Routes>
  );
}

export default CircularRoutes;
