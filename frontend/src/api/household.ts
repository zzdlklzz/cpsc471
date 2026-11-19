import { api } from "./client";
import type { Credentials, Household, HouseholdInput, MemberInput } from "../types/api";

export const getHousehold = () => api<Household>("/household");
export const updateHousehold = (data: HouseholdInput) => api<Household>("/household", "PATCH", data);
export const addMember = (data: MemberInput) => api<Household>("/household/members", "POST", data);
export const updateMember = (id: number, data: MemberInput) =>
  api<Household>(`/household/members/${id}`, "PATCH", data);
export const removeMember = (id: number) => api<Household>(`/household/members/${id}`, "DELETE");
export const enableMemberAccount = (id: number, data: Credentials) =>
  api<Household>(`/household/members/${id}/account`, "POST", data);
