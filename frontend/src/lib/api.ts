import axios, { AxiosError } from "axios";
import type { ApiError } from "./types";

export const TOKEN_KEY = "lm_token";
export const REFRESH_KEY = "lm_refresh";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshing: Promise<string> | null = null;

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as (typeof error.config & { _retry?: boolean }) | undefined;
    const refreshToken = localStorage.getItem(REFRESH_KEY);

    if (
      error.response?.status === 401 &&
      original &&
      !original._retry &&
      refreshToken &&
      !original.url?.includes("/api/auth/")
    ) {
      original._retry = true;
      try {
        refreshing ??= api
          .post("/api/auth/refresh", { refreshToken })
          .then((r) => {
            localStorage.setItem(TOKEN_KEY, r.data.token);
            localStorage.setItem(REFRESH_KEY, r.data.refreshToken);
            return r.data.token as string;
          })
          .finally(() => {
            refreshing = null;
          });
        const fresh = await refreshing;
        original.headers.set("Authorization", `Bearer ${fresh}`);
        return api(original);
      } catch {
        clearSession();
        window.location.assign("/login");
      }
    }
    return Promise.reject(error);
  },
);

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

/** Normalises any thrown value into the backend's ApiError shape. */
export function toApiError(err: unknown): ApiError {
  if (axios.isAxiosError(err) && err.response?.data && typeof err.response.data === "object") {
    return err.response.data as ApiError;
  }
  return { status: 0, error: "Network Error", message: "Could not reach the server." };
}
