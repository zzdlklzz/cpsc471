

// Use this if you have trouble using the backend

/*
import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import * as authApi from "../api/auth";
import { ApiError, fetchCsrfCookie } from "../api/client";
import type { Credentials, CurrentUser, SignupInput } from "../types/api";
import { AuthContext } from "./authContext";

// Development only: set VITE_DEV_USER=household or VITE_DEV_USER=staff in
// frontend/.env.local to skip the login page. Leave it unset for normal use.
const DEV_USERS: Record<string, CurrentUser> = {
  household: {
    role: "household",
    member_id: 1,
    staff_id: null,
    household_id: 1,
    name: "Dev Household",
    email: "dev@household.example",
  },
  staff: {
    role: "staff",
    member_id: null,
    staff_id: 1,
    household_id: null,
    name: "Dev Staff",
    email: "dev@staff.example",
  },
};
const DEV_USER: CurrentUser | null = DEV_USERS.household;
// const DEV_USER: CurrentUser | null = DEV_USERS[import.meta.env.VITE_DEV_USER ?? ""] ?? null;

export default function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(DEV_USER);
  const [loading, setLoading] = useState(DEV_USER === null);

  useEffect(() => {
    if (DEV_USER) return; // development switch is on: no server check
    // On start: get the CSRF cookie, then check for an existing session.
    fetchCsrfCookie()
      .then(() => authApi.getMe())
      .then(setUser)
      .catch((err: unknown) => {
        if (!(err instanceof ApiError) || err.status !== 401) console.error(err);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (data: Credentials) => {
    const loggedIn = await authApi.login(data);
    setUser(loggedIn);
    return loggedIn;
  }, []);

  const signup = useCallback(async (data: SignupInput) => {
    const created = await authApi.signup(data);
    setUser(created);
    return created;
  }, []);

  const logout = useCallback(async () => {
    if (!DEV_USER) await authApi.logout();
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, loading, login, signup, logout }), [user, loading, login, signup, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
} */

// Once Backend is set up
import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import * as authApi from "../api/auth";
import { ApiError, fetchCsrfCookie } from "../api/client";
import type { Credentials, CurrentUser, SignupInput } from "../types/api";
import { AuthContext } from "./authContext";

export default function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // On start: get the CSRF cookie, then check for an existing session.
    fetchCsrfCookie()
      .then(() => authApi.getMe())
      .then(setUser)
      .catch((err: unknown) => {
        if (!(err instanceof ApiError) || err.status !== 401) console.error(err);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (data: Credentials) => {
    const loggedIn = await authApi.login(data);
    setUser(loggedIn);
    return loggedIn;
  }, []);

  const signup = useCallback(async (data: SignupInput) => {
    const created = await authApi.signup(data);
    setUser(created);
    return created;
  }, []);

  const logout = useCallback(async () => {
    await authApi.logout();
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, loading, login, signup, logout }), [user, loading, login, signup, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
