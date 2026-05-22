import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../store/authStore.jsx";
import LoadingSpinner from "./LoadingSpinner.jsx";

/**
 * Restrict route to Leafy Cave owners only.
 */
function OwnerRoute({ children }) {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingSpinner message="Verifying your session…" />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/signin" state={{ from: location }} replace />;
  }

  if (user?.role !== "owner") {
    return <Navigate to="/chat" replace />;
  }

  return children;
}

export default OwnerRoute;
