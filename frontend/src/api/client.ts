import type { FieldErrors } from "../types/api";

/** Error thrown for every failed API call. `fields` holds messages for single form fields. */
export class ApiError extends Error {
  status: number;
  fields: FieldErrors;

  constructor(status: number, message: string, fields: FieldErrors = {}) {
    super(message);
    this.status = status;
    this.fields = fields;
  }
}

function getCookie(name: string): string {
  const match = document.cookie.split("; ").find((part) => part.startsWith(name + "="));
  return match ? decodeURIComponent(match.split("=")[1]) : "";
}

type Method = "GET" | "POST" | "PATCH" | "DELETE";

/** One place for all requests: adds JSON headers, the session cookie and the CSRF token. */
export async function api<T>(path: string, method: Method = "GET", body?: unknown): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (method !== "GET") {
    headers["Content-Type"] = "application/json";
    headers["X-CSRFToken"] = getCookie("csrftoken");
  }
  let response: Response;
  try {
    response = await fetch("/api" + path, {
      method,
      headers,
      credentials: "same-origin",
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "Cannot reach the server. Is Django running?");
  }
  let data: unknown = null;
  try {
    data = await response.json();
  } catch {
    // the response had no JSON body
  }
  if (!response.ok) {
    const err = (data ?? {}) as { error?: string; fields?: FieldErrors };
    throw new ApiError(response.status, err.error ?? "Something went wrong.", err.fields ?? {});
  }
  return data as T;
}

/** Call once when the app starts, so Django sets the CSRF cookie. */
export function fetchCsrfCookie(): Promise<unknown> {
  return api("/auth/csrf");
}
