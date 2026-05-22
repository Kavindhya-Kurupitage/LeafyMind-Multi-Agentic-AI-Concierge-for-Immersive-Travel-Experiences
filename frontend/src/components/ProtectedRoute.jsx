import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../store/authStore.jsx";
import LoadingSpinner from "./LoadingSpinner.jsx";

function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingSpinner message="Verifying your session…" />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/signin" state={{ from: location }} replace />;
  }

  return children;
}

export default ProtectedRoute;
