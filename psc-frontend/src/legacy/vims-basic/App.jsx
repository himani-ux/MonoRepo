

// // src/App.jsx
import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";



import Login from "./pages/Login";
import VimsHome from "./pages/VimsHome";
import CircularRoutes from "./routes/circular/CircularRoutes";
import OrbRoutes from "./routes/orb/OrbRoutes";

// Redux-based protected route
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading, isInitialized } = useAuth();

  if (!isInitialized || isLoading) {
    return null;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>

        {/* Public */}
        <Route path="/login" element={<Login />} />

        {/* Default */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Navigate to="/vims-home" replace />
            </ProtectedRoute>
          }
        />

        {/* VIMS Home */}
        <Route
          path="/vims-home"
          element={
            <ProtectedRoute>
              <VimsHome />
            </ProtectedRoute>
          }
        />

        {/* 🔥 Circular Module Routes */}
        <Route
          path="/circular/*"
          element={
            <ProtectedRoute>
              <CircularRoutes />
            </ProtectedRoute>
          }
        />

        {/* 🚢 ORB Module Routes */}
        <Route
          path="/orb/*"
          element={
            <ProtectedRoute>
              <OrbRoutes />
            </ProtectedRoute>
          }
        />

        {/* Catch-all */}
        <Route
          path="*"
          element={
            <ProtectedRoute>
              <Navigate to="/vims-home" replace />
            </ProtectedRoute>
          }
        />

      </Routes>
    </div>
  );
}

export default App;




// import ChiefDashboard from "./components/orb/files/ChiefDashboard"

// const App = () => {

//   return (
//     <ChiefDashboard />
//   )
   
// }

// export default App;
