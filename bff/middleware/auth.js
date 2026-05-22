/**
 * Bearer JWT validation middleware for protected BFF routes.
 */

import { verifyToken } from "../utils/jwt.js";

/**
 * Extract and validate Bearer token; attach decoded payload to req.user.
 */
export function validateBearerToken(req, res, next) {
  const authHeader = req.headers.authorization;

  if (!authHeader || typeof authHeader !== "string") {
    return res.status(401).json({
      detail: "Missing or invalid Authorization header",
      service: "leafymind-bff",
    });
  }

  const [scheme, token] = authHeader.split(" ");
  if (scheme?.toLowerCase() !== "bearer" || !token?.trim()) {
    return res.status(401).json({
      detail: "Missing or invalid Authorization header",
      service: "leafymind-bff",
    });
  }

  const payload = verifyToken(token.trim());
  if (!payload) {
    return res.status(401).json({
      detail: "Invalid or expired token",
      service: "leafymind-bff",
    });
  }

  req.user = payload;
  next();
}
