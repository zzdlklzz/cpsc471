import { api, ApiError } from "./client";
import type { Zone } from "../types/api";

export interface StaffEvent {
  event_id: number;
  name: string;
  event_type: "Wildfire" | "Flood";
  status: "Active" | "Closed";
  start_date: string;
  end_date: string | null;
}
export type EventInput = Omit<StaffEvent, "event_id">;
export interface StaffNotice {
  notice_id: number;
  title: string;
  message: string;
  published_at: string;
  event: StaffEvent;
  publisher: { staff_id: number; name: string };
  zones: Zone[];
}
export interface EventOverview extends StaffEvent { notices: StaffNotice[] }
export interface NoticeInput { title: string; message: string; zone_ids: number[] }
export const getStaffEvents = () => api<{ events: EventOverview[] }>("/staff/events").then(r => r.events);
export const saveEvent = (data: EventInput, id?: number) =>
  api<StaffEvent>(id === undefined ? "/staff/events" : `/staff/events/${id}`, id === undefined ? "POST" : "PATCH", data);
export const publishNotice = (event_id: number, data: NoticeInput) =>
  api<StaffNotice>("/staff/notices", "POST", { event_id, ...data });
export const editNotice = (id: number, data: NoticeInput) =>
  api<StaffNotice>(`/staff/notices/${id}`, "PATCH", data);

export function returnToLogin(error: unknown) {
  if (error instanceof ApiError && error.status === 401) window.location.assign("/login");
}

