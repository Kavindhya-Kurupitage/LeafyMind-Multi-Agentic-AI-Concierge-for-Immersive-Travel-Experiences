/**
 * Global Express error handler for the BFF layer.
 */

export function errorHandler(err, _req, res, _next) {
  console.error("[BFF Error]", err.message);
  const status = err.status || 500;
  res.status(status).json({
    message: err.message || "Internal server error",
    service: "leafymind-bff",
  });
}
