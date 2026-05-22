/**
 * JWT verification aligned with the LeafyMind FastAPI backend (HS256).
 */

import { createHmac, timingSafeEqual } from "crypto";

const JWT_SECRET = process.env.JWT_SECRET || "";
const JWT_ALGORITHM = process.env.JWT_ALGORITHM || "HS256";

function base64UrlDecode(input) {
  const padded = input + "=".repeat((4 - (input.length % 4)) % 4);
  return Buffer.from(padded.replace(/-/g, "+").replace(/_/g, "/"), "base64");
}

function decodeJsonSegment(segment) {
  try {
    return JSON.parse(base64UrlDecode(segment).toString("utf8"));
  } catch {
    return null;
  }
}

function signSegment(headerB64, payloadB64, secret) {
  const data = `${headerB64}.${payloadB64}`;
  return createHmac("sha256", secret)
    .update(data)
    .digest("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

/**
 * Verify a JWT and return its payload, or null if invalid/expired.
 * @param {string} token
 * @returns {Record<string, unknown> | null}
 */
export function verifyToken(token) {
  if (!token || !JWT_SECRET) return null;

  const parts = token.split(".");
  if (parts.length !== 3) return null;

  const [headerB64, payloadB64, signatureB64] = parts;
  const header = decodeJsonSegment(headerB64);
  const payload = decodeJsonSegment(payloadB64);

  if (!header || !payload || header.alg !== JWT_ALGORITHM) return null;

  const expectedSig = signSegment(headerB64, payloadB64, JWT_SECRET);
  const actualSigBuffer = Buffer.from(signatureB64);
  const expectedSigBuffer = Buffer.from(expectedSig);

  if (
    actualSigBuffer.length !== expectedSigBuffer.length ||
    !timingSafeEqual(actualSigBuffer, expectedSigBuffer)
  ) {
    return null;
  }

  if (payload.exp) {
    const now = Math.floor(Date.now() / 1000);
    if (now >= payload.exp) return null;
  }

  if (!payload.user_id) return null;

  return payload;
}
