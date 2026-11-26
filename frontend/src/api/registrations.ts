import { api } from "./client";
import {
  type CreateRegistrationRequest,
  type CreateRegistrationResponse,
  type RegistrationDetailResponse,
  type RegistrationListResponse,
  type ShelterListResponse,
  type UpdateParticipantsRequest,
  type UpdateParticipantsResponse,
  type CancelRegistrationResponse,
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

export function updateParticipants(
  registrationId: number,
  participants: UpdateParticipantsRequest,
): Promise<UpdateParticipantsResponse> {
  return api<UpdateParticipantsResponse>(
    "/registrations/" + registrationId + "/participants",
    "PATCH",
    participants,
  );
}

export function cancelRegistration(
  registrationId: number,
): Promise<CancelRegistrationResponse> {
  return api<CancelRegistrationResponse>(
    "/registrations/" + registrationId + "/cancel",
    "POST",
  );
}