/** JSON response types. Dates use YYYY-MM-DD strings. */
export interface HouseholdMember {
  member_id: number;
  household_id: number;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  phone_number: string | null;
  is_account_holder: boolean;
}

export interface Household {
  household_id: number;
  street: string;
  city: string;
  province: string;
  postal_code: string;
  zone_id: number;
  zone_name: string;
  members: HouseholdMember[];
}

export interface CreateMemberRequest {
  first_name: string;
  last_name: string;
  date_of_birth: string;
  phone_number?: string | null;
}

/** Omitted fields remain unchanged; null clears an optional phone number. */
export type UpdateMemberRequest = Partial<CreateMemberRequest>;

export interface UpdateHouseholdRequest {
  street?: string;
  city?: string;
  province?: string;
  postal_code?: string;
}
