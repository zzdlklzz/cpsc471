// Route names shared by the whole team. Change them here only.
export const ROUTES = {
  login: "/login",
  signup: "/signup",
  household: "/household",
  notices: "/notices",
  noticeDetails: (id: number | string) => `/notices/${id}`,
  /** Person 2's registration flow. Person 1 only links to it with the event selected. */
  shelterRegister: (eventId: number | string) => `/shelter/register?event=${eventId}`,
  shelter: "/shelter",
  staffAccommodation: "/staff/accommodation",
  staffHome: "/staff",
} as const;
