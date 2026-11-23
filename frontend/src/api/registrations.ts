import { api } from "./client";
import type {
  RegistrationDetailResponse,
  RegistrationListResponse,
} from "../types/registration";

export function getRegistrations(): Promise<RegistrationListResponse> {
  return api<RegistrationListResponse>("/registrations");
}

export function getRegistration(
  registrationId: number,
): Promise<RegistrationDetailResponse> {
  return api<RegistrationDetailResponse>(
    "/registrations/" + registrationId,
  );
}