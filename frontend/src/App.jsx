import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./store/authStore.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import GuestRoute from "./components/GuestRoute.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import SignInPage from "./pages/SignInPage.jsx";
import AgentHubPage from "./pages/AgentHubPage.jsx";
import AgentWorkspacePage from "./pages/AgentWorkspacePage.jsx";
import ChatPage from "./pages/ChatPage.jsx";
import LandingPage from "./pages/LandingPage.jsx";
import OwnerDashboard from "./pages/OwnerDashboard.jsx";
import OwnerRoute from "./components/OwnerRoute.jsx";

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route
        path="/signin"
        element={
          <GuestRoute>
            <SignInPage />
          </GuestRoute>
        }
      />
      {/* Legacy URL — never show a separate login page */}
      <Route path="/login" element={<Navigate to="/signin" replace />} />
      <Route
        path="/register"
        element={
          <GuestRoute>
            <RegisterPage />
          </GuestRoute>
        }
      />
      <Route
        path="/hub"
        element={
          <ProtectedRoute>
            <AgentHubPage />
          </ProtectedRoute>
        }
      />
      <Route path="/dashboard" element={<Navigate to="/hub" replace />} />
      <Route
        path="/agents/:agentId"
        element={
          <ProtectedRoute>
            <AgentWorkspacePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/agents/:agentId/threads/:threadId"
        element={
          <ProtectedRoute>
            <AgentWorkspacePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/chat"
        element={
          <ProtectedRoute>
            <ChatPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/owner"
        element={
          <OwnerRoute>
            <OwnerDashboard />
          </OwnerRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}

export default App;
