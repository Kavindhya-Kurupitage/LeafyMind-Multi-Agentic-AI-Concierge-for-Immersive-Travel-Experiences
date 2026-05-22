/**
 * Password strength helper for registration UI.
 */

export function getPasswordStrength(password) {
  if (!password) return { level: "weak", label: "Weak", score: 0 };

  let score = 0;
  if (password.length >= 8) score += 1;
  if (/[A-Z]/.test(password)) score += 1;
  if (/\d/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;
  if (password.length >= 12) score += 1;

  if (score <= 2) return { level: "weak", label: "Weak", score };
  if (score <= 3) return { level: "fair", label: "Fair", score };
  return { level: "strong", label: "Strong", score };
}

export const strengthColors = {
  weak: "bg-red-400",
  fair: "bg-gold",
  strong: "bg-forest-light",
};
