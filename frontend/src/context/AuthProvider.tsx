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
