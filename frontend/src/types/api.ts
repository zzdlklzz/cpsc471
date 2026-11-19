// Shapes of the JSON that the Django API returns. Keep in sync with the backend.

export type Role = "household" | "staff";

/** Shared current-user interface (agreed with Persons 2 and 3). */
export interface CurrentUser {
  role: Role;
  member_id: number | null;
  staff_id: number | null;
  household_id: number | null;
  name: string;
  email: string;
}

export interface Zone {
  zone_id: number;
  zone_name: string;
}

export interface Member {
  member_id: number;
  first_name: string;
  last_name: string;
  date_of_birth: string; // YYYY-MM-DD
  phone_number: string | null;
  is_account_holder: boolean;
  login_email: string | null;
}

export interface Household {
  household_id: number;
  street: string;
  city: string;
  province: string;
  postal_code: string;
  zone: Zone;
  members: Member[];
}

export interface HouseholdInput {
  street: string;
  city: string;
  province: string;
  postal_code: string;
  zone_id: number;
}

export interface MemberInput {
  first_name: string;
  last_name: string;
  date_of_birth: string;
  phone_number: string;
}

export interface Credentials {
  login_email: string;
  password: string;
}

export type SignupInput = HouseholdInput & MemberInput & Credentials;

export interface EventSummary {
  event_id: number;
  name: string;
  event_type: string;
  status: string;
  start_date?: string;
  end_date?: string | null;
}

export interface Notice {
  notice_id: number;
  title: string;
  message: string;
  published_at: string;
  event: EventSummary;
  zones: Zone[];
  targets_my_zone: boolean;
  can_register: boolean;
}

export type FieldErrors = Record<string, string>;
