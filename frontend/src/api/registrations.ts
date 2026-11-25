import { api } from "./client";
import type {
  CreateRegistrationRequest,
  CreateRegistrationResponse,
  RegistrationDetailResponse,
  RegistrationListResponse,
  ShelterListResponse,
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

export function getShelters(
  groupSize: number,
): Promise<ShelterListResponse> {
  return api<ShelterListResponse>(
    "/shelters?group_size=" + groupSize,
  );
}

export function createRegistration(
  reservation: CreateRegistrationRequest,
): Promise<CreateRegistrationResponse> {
  return api<CreateRegistrationResponse>(
    "/registrations/create",
    "POST",
    reservation,
  );
}