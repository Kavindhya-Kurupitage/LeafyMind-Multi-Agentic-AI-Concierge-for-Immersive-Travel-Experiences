import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import AuthLayout from "../components/AuthLayout.jsx";
import LeafyCaveLogo from "../components/brand/LeafyCaveLogo.jsx";
import { useAuth } from "../store/authStore.jsx";
import { getErrorMessage } from "../utils/api.js";
import { getPasswordStrength, strengthColors } from "../utils/passwordStrength.js";
import { sanitizeRegistrationPayload } from "../utils/sanitize.js";

function RegisterPage() {
  const navigate = useNavigate();
  const { register, isLoading } = useAuth();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [bannerError, setBannerError] = useState("");

  const strength = getPasswordStrength(password);

  const validate = () => {
    const errors = {};
    if (!fullName.trim()) errors.fullName = "Full name is required";
    if (!email.trim()) {
      errors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = "Enter a valid email address";
    }
    if (!password) {
      errors.password = "Password is required";
    } else if (password.length < 8) {
      errors.password = "Password must be at least 8 characters";
    } else if (!/[A-Z]/.test(password) || !/\d/.test(password)) {
      errors.password = "Include at least one uppercase letter and one number";
    }
    if (password !== confirmPassword) {
      errors.confirmPassword = "Passwords do not match";
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setBannerError("");
    if (!validate()) return;

    try {
      await register(
        sanitizeRegistrationPayload({
          email,
          password,
          full_name: fullName,
        })
      );
      navigate("/hub", { replace: true });
    } catch (err) {
      setBannerError(getErrorMessage(err));
    }
  };

  return (
    <AuthLayout>
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <div className="mb-6 flex justify-center lg:justify-start">
          <LeafyCaveLogo to={null} size="md" showWordmark={false} />
        </div>
        <h2 className="font-display text-3xl font-semibold text-forest">Create your account</h2>
        <p className="mt-2 text-sm text-forest/60">
          Join Leafy Cave and let our AI concierge craft your perfect stay.
        </p>

        {bannerError && (
          <div className="auth-error mt-6 animate-fade-in" role="alert">
            {bannerError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-8 space-y-5" noValidate>
          <div>
            <label htmlFor="fullName" className="mb-1.5 block text-sm font-medium text-forest">
              Full Name
            </label>
            <input
              id="fullName"
              type="text"
              autoComplete="name"
              maxLength={255}
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="input-field"
              placeholder="Jane Smith"
            />
            {fieldErrors.fullName && (
              <p className="mt-1.5 text-sm text-red-600">{fieldErrors.fullName}</p>
            )}
          </div>

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
            {fieldErrors.email && (
              <p className="mt-1.5 text-sm text-red-600">{fieldErrors.email}</p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-forest">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field"
              placeholder="••••••••"
            />
            {password && (
              <div className="mt-2">
                <div className="flex gap-1">
                  {[1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className={`h-1 flex-1 rounded-full transition-colors ${
                        strength.score >= i
                          ? strengthColors[strength.level]
                          : "bg-cream-dark"
                      }`}
                    />
                  ))}
                </div>
                <p className="mt-1 text-xs text-forest/60">
                  Strength: <span className="font-medium capitalize">{strength.label}</span>
                </p>
              </div>
            )}
            {fieldErrors.password && (
              <p className="mt-1.5 text-sm text-red-600">{fieldErrors.password}</p>
            )}
          </div>

          <div>
            <label
              htmlFor="confirmPassword"
              className="mb-1.5 block text-sm font-medium text-forest"
            >
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              autoComplete="new-password"
              maxLength={128}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="input-field"
              placeholder="••••••••"
            />
            {fieldErrors.confirmPassword && (
              <p className="mt-1.5 text-sm text-red-600">{fieldErrors.confirmPassword}</p>
            )}
          </div>

          <button type="submit" className="btn-gold w-full" disabled={isLoading}>
            {isLoading ? "Creating account…" : "Create Account"}
          </button>
        </form>

        <p className="mt-8 text-center text-sm text-forest/60">
          Already have an account?{" "}
          <Link to="/signin" className="font-medium text-forest-light hover:text-gold">
            Sign in
          </Link>
        </p>
        <p className="mt-3 text-center text-sm text-forest/50">
          <Link to="/" className="hover:text-forest">
            ← Back to home
          </Link>
        </p>
      </motion.div>
    </AuthLayout>
  );
}

export default RegisterPage;
