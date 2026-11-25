export interface Registration {
  registration_id: number;
  event_id: number;
  status: string;
  submitted_at: string;
  event_name: string;
}

export interface RegistrationListResponse {
  registrations: Registration[];
}

export interface RegistrationParticipant {
  member_id: number;
  first_name: string;
  last_name: string;
}

export interface RegistrationPlacement {
  placement_no: number;
  shelter_name: string;
  status: string;
  arrival_time: string | null;
  departure_time: string | null;
}

export interface RegistrationDetailResponse {
  registration: Registration;
  participants: RegistrationParticipant[];
  placements: RegistrationPlacement[];
}

export interface Shelter {
  shelter_id: number;
  name: string;
  address: string;
  available_spaces: number;
}

export interface ShelterListResponse {
  shelters: Shelter[];
}

export interface CreateRegistrationRequest {
  event_id: number;
  shelter_id: number;
  member_ids: number[];
}

export interface CreateRegistrationResponse {
  registration_id: number;
  message: string;
}

export interface UpdateParticipantsRequest {
  member_ids: number[];
}

export interface UpdateParticipantsResponse {
  message: string;
}

export interface CancelRegistrationResponse {
  message: string;
}