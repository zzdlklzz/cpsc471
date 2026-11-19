import { createContext, useContext } from "react";
import type { Credentials, CurrentUser, SignupInput } from "../types/api";

export interface AuthValue {
  user: CurrentUser | null;
  loading: boolean; // true while we ask the server who is logged in
  login: (data: Credentials) => Promise<CurrentUser>;
  signup: (data: SignupInput) => Promise<CurrentUser>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthValue | null>(null);

/** Shared current-user hook. Persons 2 and 3 use this in their pages. */
export function useAuth(): AuthValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
