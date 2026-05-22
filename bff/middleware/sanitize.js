/**
 * Sanitises string fields in JSON request bodies before proxying to the backend.
 */

const HTML_TAG_PATTERN = /<[^>]*>/g;
const MAX_STRING_LENGTH = 2000;

function sanitiseString(value) {
  if (typeof value !== "string") return value;
  return value.replace(HTML_TAG_PATTERN, "").trim().slice(0, MAX_STRING_LENGTH);
}

function sanitiseValue(value) {
  if (typeof value === "string") return sanitiseString(value);
  if (Array.isArray(value)) return value.map(sanitiseValue);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, val]) => [key, sanitiseValue(val)])
    );
  }
  return value;
}

/**
 * Strip HTML tags and cap string lengths on POST request bodies.
 */
export function sanitizeInput(req, res, next) {
  if (req.method !== "POST") {
    return next();
  }

  if (req.body && typeof req.body === "object") {
    req.body = sanitiseValue(req.body);
  }

  next();
}
