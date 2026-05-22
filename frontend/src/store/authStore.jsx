/**
 * Authentication state via React Context + useReducer.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer,
} from "react";
import { authAPI, configureApiAuth } from "../utils/api.js";

const TOKEN_KEY = "leafymind_token";

const initialState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

function authReducer(state, action) {
  switch (action.type) {
    case "LOGIN":
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };
    case "LOGOUT":
      return {
        ...initialState,
        isLoading: false,
      };
    case "SET_LOADING":
      return {
        ...state,
        isLoading: action.payload,
      };
    case "SET_ERROR":
      return {
        ...state,
        error: action.payload,
        isLoading: false,
      };
    case "RESTORE_SESSION":
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };
    default:
      return state;
  }
}

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  const logout = useCallback(async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      try {
        await authAPI.logout();
      } catch {
        /* still clear local session if revoke request fails */
      }
    }
    localStorage.removeItem(TOKEN_KEY);
    dispatch({ type: "LOGOUT" });
  }, []);

  const login = useCallback(async (email, password) => {
    dispatch({ type: "SET_LOADING", payload: true });
    dispatch({ type: "SET_ERROR", payload: null });
    try {
      const data = await authAPI.login(email, password);
      localStorage.setItem(TOKEN_KEY, data.access_token);
      dispatch({
        type: "LOGIN",
        payload: {
          token: data.access_token,
          user: data.user,
        },
      });
      return data;
    } catch (err) {
      const status = err.response?.status;
      let message = err.response?.data?.detail || "Login failed. Please try again.";
      if (err.code === "ECONNABORTED" || /timeout/i.test(err.message || "")) {
        message = "The server is slow or still starting. Wait a few seconds and try again.";
      } else if (status === 503 || status === 504) {
        message =
          typeof message === "string" && message.length > 10
            ? message
            : "The server is starting or busy. Wait a few seconds and try again.";
      }
      dispatch({ type: "SET_ERROR", payload: message });
      throw err;
    }
  }, []);

  const register = useCallback(async (payload) => {
    dispatch({ type: "SET_LOADING", payload: true });
    dispatch({ type: "SET_ERROR", payload: null });
    try {
      await authAPI.register(payload);
      const data = await authAPI.login(payload.email, payload.password);
      localStorage.setItem(TOKEN_KEY, data.access_token);
      dispatch({
        type: "LOGIN",
        payload: {
          token: data.access_token,
          user: data.user,
        },
      });
      return data;
    } catch (err) {
      const message = err.response?.data?.detail || "Registration failed. Please try again.";
      dispatch({ type: "SET_ERROR", payload: message });
      throw err;
    }
  }, []);

  useEffect(() => {
    configureApiAuth({
      getToken: () => localStorage.getItem(TOKEN_KEY),
      onUnauthorized: () => dispatch({ type: "LOGOUT" }),
    });
  }, []);

  useEffect(() => {
    const restore = async () => {
      const token = localStorage.getItem(TOKEN_KEY);
      if (!token) {
        dispatch({ type: "SET_LOADING", payload: false });
        return;
      }

      dispatch({ type: "SET_LOADING", payload: true });
      try {
        const user = await authAPI.me();
        dispatch({
          type: "RESTORE_SESSION",
          payload: { token, user },
        });
      } catch {
        localStorage.removeItem(TOKEN_KEY);
        dispatch({ type: "LOGOUT" });
      }
    };

    restore();
  }, []);

  const value = useMemo(
    () => ({
      ...state,
      dispatch,
      login,
      register,
      logout,
    }),
    [state, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
