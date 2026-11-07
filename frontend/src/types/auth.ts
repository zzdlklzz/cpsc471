import type { CreateMemberRequest } from './household';

/** Use CurrentUser | null for an unauthenticated frontend state. */
export interface CurrentUser {
  role: 'household';
  member_id: number;
  household_id: number;
}

/** Household signup only; the backend assigns IDs and the demo zone. */
export interface SignupRequest extends CreateMemberRequest {
  login_email: string;
  password: string;
  street: string;
  city: string;
  province: string;
  postal_code: string;
}

export interface EnableAccountRequest {
  login_email: string;
  password: string;
}
