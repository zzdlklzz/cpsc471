import { Navigate, Route, Routes } from "./router";
import NavBar from "./components/NavBar";
import ProtectedRoute from "./components/ProtectedRoute";
import { useAuth } from "./context/authContext";
import LoginPage from "./pages/LoginPage";
import MyHouseholdPage from "./pages/MyHouseholdPage";
import NoticeDetailsPage from "./pages/NoticeDetailsPage";
import NoticesPage from "./pages/NoticesPage";
import PlaceholderPage from "./pages/PlaceholderPage";
import SignUpPage from "./pages/SignUpPage";
import { ROUTES } from "./routes";
import MyShelterPage from "./pages/MyShelterPage";
import RegistrationDetailsPage from "./pages/RegistrationDetailsPage";
import RegisterShelterPage from "./pages/RegisterShelterPage";

export default function App() {
  const { user, loading } = useAuth();
  const home = !user ? ROUTES.login : user.role === "staff" ? ROUTES.staffHome : ROUTES.household;

  return (
    <>
      <NavBar />
      <main>
        {loading ? (
          <p className="muted">Loading...</p>
        ) : (
          <Routes>
            <Route path={ROUTES.login} element={<LoginPage />} />
            <Route path={ROUTES.signup} element={<SignUpPage />} />

            {/* Household pages */}
            <Route element={<ProtectedRoute role="household" />}>
              <Route path={ROUTES.household} element={<MyHouseholdPage />} />
              <Route path={ROUTES.notices} element={<NoticesPage />} />
              <Route path="/notices/:id" element={<NoticeDetailsPage />} />
              {/* Person 2 replaces these two placeholders */}
              <Route path={ROUTES.shelter} element={<MyShelterPage />} />
              <Route path="/shelter/registrations/:id" element={<RegistrationDetailsPage />}/>
              <Route path="/shelter/register" element={<RegisterShelterPage />} />
            </Route>

            {/* Staff pages. Person 3 replaces this placeholder */}
            <Route element={<ProtectedRoute role="staff" />}>
              <Route path={ROUTES.staffHome} element={<PlaceholderPage title="Staff Home" owner="Person 3" />} />
            </Route>

            <Route path="*" element={<Navigate to={home} replace />} />
          </Routes>
        )}
      </main>
    </>
  );
}
