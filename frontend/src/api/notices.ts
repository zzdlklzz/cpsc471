import { api } from "./client";
import type { EventSummary, Notice } from "../types/api";

export interface NoticeFilters {
  scope: "mine" | "all";
  eventId: string; // "" means no filter
  zoneId: string;
}

export function getNotices(filters: NoticeFilters): Promise<Notice[]> {
  const params = new URLSearchParams({ scope: filters.scope });
  if (filters.eventId) params.set("event", filters.eventId);
  if (filters.zoneId) params.set("zone", filters.zoneId);
  return api<{ notices: Notice[] }>(`/notices?${params.toString()}`).then((r) => r.notices);
}

export const getNotice = (id: number) => api<Notice>(`/notices/${id}`);
export const getEvents = () => api<{ events: EventSummary[] }>("/events").then((r) => r.events);
