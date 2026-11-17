import { Navigate, Outlet } from "../router";
import { useAuth } from "../context/authContext";
import { ROUTES } from "../routes";
import type { Role } from "../types/api";

/** Shows the child pages only for a logged-in user with the right role. */
export default function ProtectedRoute({ role }: { role?: Role }) {
  const { user, loading } = useAuth();
  if (loading) return <p className="muted">Loading...</p>;
  if (!user) return <Navigate to={ROUTES.login} replace />;
  if (role && user.role !== role) {
    return <Navigate to={user.role === "staff" ? ROUTES.staffHome : ROUTES.household} replace />;
  }
  return <Outlet />;
}
