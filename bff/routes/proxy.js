/**
 * HTTP proxy middleware from /api/* to the FastAPI backend.
 */

import { createProxyMiddleware } from "http-proxy-middleware";

/**
 * Proxy /api/* to FastAPI (paths without the /api prefix).
 *
 * @param {string} backendUrl - FastAPI base URL, e.g. http://backend:8000
 */
export function createApiProxy(backendUrl) {
  return createProxyMiddleware({
    target: backendUrl,
    changeOrigin: true,
    pathRewrite: { "^/api": "" },
    proxyTimeout: 120_000,
    timeout: 120_000,
    on: {
      proxyReq: (proxyReq, req) => {
        if (req.headers.authorization) {
          proxyReq.setHeader("Authorization", req.headers.authorization);
        }
      },
      proxyRes: (proxyRes) => {
        proxyRes.headers["x-powered-by"] = "leafymind-bff";
      },
      error: (err, req, res) => {
        console.error("[BFF Proxy]", err.code || err.message, req.method, req.url);
        if (!res.headersSent) {
          const starting =
            err.code === "ECONNREFUSED" ||
            err.code === "ECONNRESET" ||
            err.code === "ENOTFOUND";
          res.statusCode = starting ? 503 : 504;
          res.setHeader("Content-Type", "application/json");
          res.end(
            JSON.stringify({
              detail: starting
                ? "LeafyMind API is starting up. Wait a few seconds and try again."
                : "Request to the API timed out. Please try again.",
            })
          );
        }
      },
    },
  });
}
