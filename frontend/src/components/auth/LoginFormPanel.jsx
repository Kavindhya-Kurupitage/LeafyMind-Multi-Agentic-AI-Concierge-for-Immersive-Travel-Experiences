import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import LeafyCaveLogo from "../brand/LeafyCaveLogo.jsx";
import { useAuth } from "../../store/authStore.jsx";
import { getErrorMessage } from "../../utils/api.js";
import { sanitizeEmail } from "../../utils/sanitize.js";

function LoginFormPanel({ onBack = "/" }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isLoading } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [bannerError, setBannerError] = useState("");

  const validate = () => {
    const errors = {};
    if (!email.trim()) errors.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.email = "Enter a valid email address";
    if (!password) errors.password = "Password is required";
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setBannerError("");
    if (!validate()) return;
    try {
      await login(sanitizeEmail(email), password.slice(0, 128));
      const redirectTo = location.state?.from?.pathname || "/hub";
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setBannerError(getErrorMessage(err));
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full"
    >
      {onBack && (
        <button
          type="button"
          onClick={() => navigate(typeof onBack === "string" ? onBack : "/", { replace: true })}
          className="mb-6 flex items-center gap-2 text-sm text-forest/60 transition hover:text-forest"
        >
          <span aria-hidden="true">←</span> Back to home
        </button>
      )}

      <div className="mb-6 flex justify-center lg:justify-start">
        <LeafyCaveLogo to={null} size="md" showWordmark={false} />
      </div>

      <h2 className="font-display text-3xl font-semibold text-forest">Welcome back</h2>
      <p className="mt-2 text-sm text-forest/60">
        Sign in to continue planning your Sri Lankan escape.
      </p>

      {bannerError && (
        <div className="auth-error mt-6" role="alert">
          {bannerError}
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-8 space-y-5" noValidate>
        <div>
          <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-forest">
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            maxLength={255}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input-field"
            placeholder="you@example.com"
          />
          {fieldErrors.email && <p className="mt-1.5 text-sm text-red-600">{fieldErrors.email}</p>}
        </div>

        <div>
          <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-forest">
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            maxLength={128}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input-field"
            placeholder="••••••••"
          />
          {fieldErrors.password && (
            <p className="mt-1.5 text-sm text-red-600">{fieldErrors.password}</p>
          )}
        </div>

        <button type="submit" className="btn-gold w-full" disabled={isLoading}>
          {isLoading ? "Signing in…" : "Sign In"}
        </button>
      </form>

      <p className="mt-8 text-center text-sm text-forest/60">
        New to Leafy Cave?{" "}
        <Link to="/register" className="font-medium text-forest-light hover:text-gold">
          Create an account
        </Link>
      </p>
    </motion.div>
  );
}

export default LoginFormPanel;
