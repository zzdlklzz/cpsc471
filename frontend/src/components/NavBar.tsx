import { NavLink, useNavigate } from "../router";
import { useAuth } from "../context/authContext";
import { ROUTES } from "../routes";

/** Shared navigation. Persons 2 and 3 add their own links in the marked places. */
export default function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate(ROUTES.login);
  }

  return (
    <header className="navbar">
      <span className="brand">EvacBridge</span>
      <nav>
        {user?.role === "household" && (
          <>
            <NavLink to={ROUTES.household}>My Household</NavLink>
            <NavLink to={ROUTES.notices}>Notices</NavLink>
            <NavLink to={ROUTES.shelter}>My Shelter</NavLink> {/* Person 2 */}
          </>
        )}
        {user?.role === "staff" && (
          <>
            <NavLink to={ROUTES.staffHome} end>Events &amp; Notices</NavLink> <NavLink to={ROUTES.staffAccommodation}>Accommodation</NavLink>
          </>
        )}
        {!user && (
          <>
            <NavLink to={ROUTES.login}>Log in</NavLink>
            <NavLink to={ROUTES.signup}>Sign up</NavLink>
          </>
        )}
      </nav>
      {user && (
        <div className="nav-user">
          <span>{user.name}</span>
          <button type="button" className="secondary" onClick={handleLogout}>
            Log out
          </button>
        </div>
      )}
    </header>
  );
}
