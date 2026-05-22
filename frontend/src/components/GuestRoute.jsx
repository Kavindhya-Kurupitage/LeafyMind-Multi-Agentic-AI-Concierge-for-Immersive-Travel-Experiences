import { Navigate } from "react-router-dom";
import { useAuth } from "../store/authStore.jsx";
import LoadingSpinner from "./LoadingSpinner.jsx";

/**
 * Redirect authenticated users away from login/register pages.
 */
function GuestRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSpinner message="Loading…" />;
  }

  if (isAuthenticated) {
    return <Navigate to="/hub" replace />;
  }

  return children;
}

export default GuestRoute;
