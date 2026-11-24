import { Children, isValidElement, useCallback, useEffect, useMemo, useState } from "react";
import type { MouseEvent, ReactNode } from "react";
import { LocationContext, OutletContext, ParamsContext, useLocationValue } from "./context";
import type { NavigateFn } from "./context";

function currentUrl(): string {
  return window.location.pathname + window.location.search;
}

export function BrowserRouter({ children }: { children: ReactNode }) {
  const [url, setUrl] = useState(currentUrl);

  useEffect(() => {
    // Browser back and forward buttons
    const onPopState = () => setUrl(currentUrl());
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const navigate = useCallback<NavigateFn>((to, options) => {
    if (options?.replace) window.history.replaceState({}, "", to);
    else window.history.pushState({}, "", to);
    setUrl(to);
  }, []);

  const value = useMemo(() => {
    const [pathname, search = ""] = url.split("?");
    return { pathname, search, navigate };
  }, [url, navigate]);

  return <LocationContext.Provider value={value}>{children}</LocationContext.Provider>;
}

interface RouteProps {
  path?: string;
  element?: ReactNode;
  children?: ReactNode;
}

/** Declares one route. <Routes> reads its props. It draws nothing by itself. */
export function Route(props: RouteProps) {
  void props;
  return null;
}

/** Returns the ":name" values if the pattern matches the path, otherwise null. */
function matchPath(pattern: string, pathname: string): Record<string, string> | null {
  if (pattern === "*") return {};
  const want = pattern.split("/").filter(Boolean);
  const have = pathname.split("/").filter(Boolean);
  if (want.length !== have.length) return null;
  const params: Record<string, string> = {};
  for (let i = 0; i < want.length; i++) {
    if (want[i].startsWith(":")) params[want[i].slice(1)] = decodeURIComponent(have[i]);
    else if (want[i] !== have[i]) return null;
  }
  return params;
}

interface Match {
  params: Record<string, string>;
  node: ReactNode;
}

function findMatch(children: ReactNode, pathname: string): Match | null {
  for (const child of Children.toArray(children)) {
    if (!isValidElement(child)) continue;
    const { path, element, children: nested } = child.props as RouteProps;
    if (path === undefined) {
      // A layout route such as <Route element={<ProtectedRoute />}> with child routes
      const inner = nested ? findMatch(nested, pathname) : null;
      if (inner) {
        return { params: inner.params, node: <OutletContext.Provider value={inner.node}>{element}</OutletContext.Provider> };
      }
      continue;
    }
    const params = matchPath(path, pathname);
    if (params) return { params, node: element };
  }
  return null;
}

/** Shows the first <Route> whose path matches the current address. */
export function Routes({ children }: { children: ReactNode }) {
  const { pathname } = useLocationValue();
  const match = findMatch(children, pathname);
  if (!match) return null;
  return <ParamsContext.Provider value={match.params}>{match.node}</ParamsContext.Provider>;
}

/** Inside a layout route: the place where the matched child page appears. */
export function Outlet() {
  return <OutletContext.Consumer>{(node) => node}</OutletContext.Consumer>;
}

/** Redirects as soon as it is shown. */
export function Navigate({ to, replace = false }: { to: string; replace?: boolean }) {
  const { navigate } = useLocationValue();
  useEffect(() => {
    navigate(to, { replace });
  }, [navigate, to, replace]);
  return null;
}

interface LinkProps {
  to: string;
  children: ReactNode;
  className?: string;
}

export function Link({ to, children, className }: LinkProps) {
  const { navigate } = useLocationValue();
  function handleClick(event: MouseEvent<HTMLAnchorElement>) {
    // Let the browser handle ctrl-click, middle-click and similar
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    navigate(to);
  }
  return (
    <a href={to} className={className} onClick={handleClick}>
      {children}
    </a>
  );
}

/** A link that gets the class "active" while its page is open. */
export function NavLink({ to, children, end = false }: { to: string; children: ReactNode; end?: boolean }) {
  const { pathname } = useLocationValue();
  const active = pathname === to || (!end && pathname.startsWith(to + "/"));
  return (
    <Link to={to} className={active ? "active" : undefined}>
      {children}
    </Link>
  );
}
