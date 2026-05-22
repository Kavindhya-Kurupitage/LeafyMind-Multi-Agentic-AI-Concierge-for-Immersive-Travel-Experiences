import "dotenv/config";
import http from "http";
import express from "express";
import cors from "cors";
import helmet from "helmet";
import morgan from "morgan";
import rateLimit from "express-rate-limit";
import expressWs from "express-ws";
import { v4 as uuidv4 } from "uuid";
import { parse as parseUrl } from "url";

import { createApiProxy } from "./routes/proxy.js";
import { errorHandler } from "./middleware/errorHandler.js";
import { verifyToken } from "./utils/jwt.js";

const PORT = Number(process.env.BFF_PORT) || 3001;
const backendUrl = process.env.BFF_BACKEND_URL || "http://localhost:8000";

const allowedOrigins = (process.env.CORS_ALLOWED_ORIGINS || "http://localhost:5173")
  .split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);

const app = express();
const server = http.createServer(app);
expressWs(app, server);

app.use(helmet());
app.use(morgan(process.env.NODE_ENV === "production" ? "combined" : "dev"));
app.use(
  cors({
    origin: allowedOrigins,
    credentials: true,
  })
);

const globalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  standardHeaders: true,
  legacyHeaders: false,
  message: { detail: "Too many requests, please try again later." },
  skip: (req) => {
    const path = req.path || "";
    return path.startsWith("/api/trip-pack");
  },
});

const authLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 10,
  standardHeaders: true,
  legacyHeaders: false,
  message: { detail: "Too many authentication attempts, please try again later." },
});

app.use(globalLimiter);

app.get("/health", (_req, res) => {
  res.status(200).json({ status: "healthy", service: "leafymind-bff" });
});

// Proxy before express.json() so POST bodies stream through to FastAPI intact.
app.use("/api/auth", authLimiter);
app.use("/api", createApiProxy(backendUrl));

/**
 * Stream a text reply to the WebSocket client in chunks.
 */
async function streamReplyToClient(ws, text) {
  const chunkSize = 80;
  for (let i = 0; i < text.length; i += chunkSize) {
    if (ws.readyState !== ws.OPEN) return;
    ws.send(
      JSON.stringify({
        type: "chunk",
        content: text.slice(i, i + chunkSize),
      })
    );
    await new Promise((resolve) => setTimeout(resolve, 15));
  }
  if (ws.readyState === ws.OPEN) {
    ws.send(JSON.stringify({ type: "done" }));
  }
}

app.ws("/ws/chat", (ws, req) => {
  const { query } = parseUrl(req.url, true);
  const token = typeof query.token === "string" ? query.token : null;

  const payload = token ? verifyToken(token) : null;
  if (!payload) {
    ws.close(4001, "Unauthorized");
    return;
  }

  const connectionId = uuidv4();
  console.log(`[WS] Connected connectionId=${connectionId} userId=${payload.user_id}`);

  ws.on("message", async (raw) => {
    try {
      const message = JSON.parse(raw.toString());

      const response = await fetch(`${backendUrl}/chat/message`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(message),
      });

      const body = await response.json().catch(() => ({}));

      if (!response.ok) {
        ws.send(
          JSON.stringify({
            type: "error",
            message: body.detail || "Failed to process message",
          })
        );
        return;
      }

      const reply = body.reply || "";
      await streamReplyToClient(ws, reply);
    } catch (err) {
      console.error(`[WS] Error connectionId=${connectionId}`, err.message);
      if (ws.readyState === ws.OPEN) {
        ws.send(JSON.stringify({ type: "error", message: "Failed to process message" }));
      }
    }
  });

  ws.on("close", () => {
    console.log(`[WS] Disconnected connectionId=${connectionId} userId=${payload.user_id}`);
  });

  ws.on("error", (err) => {
    console.error(`[WS] Socket error connectionId=${connectionId}`, err.message);
  });
});

app.use(errorHandler);

server.listen(PORT, "0.0.0.0", () => {
  console.log(`LeafyMind BFF listening on port ${PORT}`);
  console.log(`Proxying API requests to ${backendUrl}`);
});
