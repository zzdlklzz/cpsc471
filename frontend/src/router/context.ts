// A very small client-side router with the same names as react-router-dom
// (BrowserRouter, Routes, Route, Link, useNavigate, ...). It keeps the project
// free of an extra dependency. To switch to react-router-dom later, change the
// imports from "../router" to "react-router-dom".
import { createContext, useContext } from "react";
import type { ReactNode } from "react";

export interface NavigateOptions {
  replace?: boolean;
}
export type NavigateFn = (to: string, options?: NavigateOptions) => void;

export interface LocationValue {
  pathname: string;
  search: string;
  navigate: NavigateFn;
}

export const LocationContext = createContext<LocationValue | null>(null);
export const OutletContext = createContext<ReactNode>(null);
export const ParamsContext = createContext<Record<string, string>>({});

export function useLocationValue(): LocationValue {
  const value = useContext(LocationContext);
  if (!value) throw new Error("Router hooks must be used inside <BrowserRouter>");
  return value;
}

/** Returns a function that changes the page without reloading it. */
export function useNavigate(): NavigateFn {
  return useLocationValue().navigate;
}

/** Values of the ":name" parts of the matched route path. */
export function useParams(): Record<string, string | undefined> {
  return useContext(ParamsContext);
}

/** The query string, for example ?event=3. */
export function useSearchParams(): [URLSearchParams] {
  return [new URLSearchParams(useLocationValue().search)];
}
