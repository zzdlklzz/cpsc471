import { api } from "./client";
import type { Credentials, CurrentUser, SignupInput, Zone } from "../types/api";

export const getMe = () => api<CurrentUser>("/auth/me");
export const login = (data: Credentials) => api<CurrentUser>("/auth/login", "POST", data);
export const logout = () => api<{ detail: string }>("/auth/logout", "POST", {});
export const signup = (data: SignupInput) => api<CurrentUser>("/auth/signup", "POST", data);
export const getZones = () => api<{ zones: Zone[] }>("/zones").then((r) => r.zones);
