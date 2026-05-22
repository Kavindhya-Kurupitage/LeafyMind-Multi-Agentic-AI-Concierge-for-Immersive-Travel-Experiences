import { Navigate } from "react-router-dom";
import AuthLayout from "../components/AuthLayout.jsx";
import LoginFormPanel from "../components/auth/LoginFormPanel.jsx";
import { useAuth } from "../store/authStore.jsx";
import LoadingSpinner from "../components/LoadingSpinner.jsx";

/**
 * Direct email/password sign-in — no marketing interstitial.
 */
function SignInPage() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSpinner message="Loading…" />;
  }

  if (isAuthenticated) {
    return <Navigate to="/hub" replace />;
  }

  return (
    <AuthLayout>
      <LoginFormPanel onBack="/" />
    </AuthLayout>
  );
}

export default SignInPage;
