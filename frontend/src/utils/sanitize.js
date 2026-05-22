/**
 * Client-side input sanitisation before API submission.
 */

const HTML_TAG_RE = /<[^>]*>/g;
const CONTROL_CHAR_RE = /[\u0000-\u001F\u007F]/g;

export function sanitizeText(value, maxLength = 255) {
  if (typeof value !== "string") return "";
  return value
    .replace(HTML_TAG_RE, "")
    .replace(CONTROL_CHAR_RE, "")
    .trim()
    .slice(0, maxLength);
}

export function sanitizeEmail(value) {
  return sanitizeText(value, 255).toLowerCase();
}

export function sanitizeRegistrationPayload({ email, password, full_name }) {
  return {
    email: sanitizeEmail(email),
    password: password.slice(0, 128),
    full_name: sanitizeText(full_name, 255),
  };
}
