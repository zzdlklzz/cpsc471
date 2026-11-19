# Person 1 Plan: Accounts, Household Information, Notices

Status key: **Done** = written and checked here. **Unverified** = written but could not be run here (see "What was and was not tested").

## 1. Requirements review (from the requirements file)

| # | Requirement | Pages / tables |
|---|---|---|
| 1 | Login, logout, staff vs household role | Login. Reads ACCOUNT_HOLDER, STAFF |
| 2 | Household sign up (household + first member + account together) | Sign Up. Writes HOUSEHOLD, HOUSEHOLD_MEMBER, ACCOUNT_HOLDER |
| 3 | View household info and members | My Household |
| 4 | Edit address and zone (predefined zones) | Edit Household. Reads EVACUATION_ZONE |
| 5 | Add, edit, remove member (only if not referenced, keep at least one account holder) | Add / Edit Member |
| 6 | Give another member a login | Enable Member Account |
| 7 to 9 | Notices: newest first, filter by event or zone, details | Notices, Notice Details. Reads EVACUATION_NOTICE, NOTICE_ZONE, EMERGENCY_EVENT |
| 10 | "Register for Shelter" button opens Person 2's flow with the event selected | Notice Details |
| Shared | App skeleton, DB connection, navigation, seed data. Preloaded staff and zones. No staff signup. Access checks for everyone | |

Boundary: Person 1 never creates events or notices and never reserves spaces.

## 2. Folder structure

```
backend/
  sql/                  schema-v1.sql (team schema), seed-v1.sql, README.md
  config/               settings.py, urls.py
  core/                 SHARED: models.py, auth_helpers.py, test_runner.py, testing.py
    management/commands/ check_schema.py, set_demo_passwords.py
  accounts/             Person 1: views.py, serializers.py, urls.py, tests.py
  notices/              Person 1: views.py, urls.py, tests.py
frontend/src/
  api/                  client.ts (fetch + CSRF), auth.ts, household.ts, notices.ts
  types/api.ts          TypeScript interfaces for the API
  context/              authContext.ts (useAuth), AuthProvider.tsx
  router/               small built-in router (same names as react-router-dom)
  components/           NavBar, ProtectedRoute, form fields
  pages/                Login, SignUp, MyHousehold, Notices, NoticeDetails, Placeholder
  routes.ts             shared route names
```

## 3. Models Person 1 needs (all `managed = False`, tables come from backend/sql/schema-v1.sql)

| Model | Table | Key points |
|---|---|---|
| EvacuationZone | EVACUATION_ZONE | read only |
| Household | HOUSEHOLD | FK zone |
| HouseholdMember | HOUSEHOLD_MEMBER | FK household |
| AccountHolder | ACCOUNT_HOLDER | primary key is the member (one to one) |
| Staff | STAFF | read only, preloaded |
| EmergencyEvent | EMERGENCY_EVENT | read only for Person 1 |
| EvacuationNotice | EVACUATION_NOTICE | read only for Person 1 |
| NoticeZone | NOTICE_ZONE | composite primary key (notice_id, zone_id) |

Written in `backend/core/models.py`. Models for REGISTRATION, PLACEMENT, SHELTER and the others belong to Persons 2 and 3.

## 4. API endpoints

| Method and path | Who can call | What it does |
|---|---|---|
| POST /api/auth/login | anyone | Checks STAFF first, then ACCOUNT_HOLDER. Returns the current user |
| POST /api/auth/logout | logged in | Clears the session |
| GET /api/auth/me | logged in | Current user: role, member_id or staff_id, household_id |
| POST /api/auth/signup | anyone | Creates household + member + account in one transaction. Never creates staff |
| GET /api/zones | anyone | List of predefined zones (needed by the sign-up form) |
| GET /api/household | account holder | Own household, zone, members, account-holder flags |
| PATCH /api/household | account holder | Update address and zone |
| POST /api/household/members | account holder | Add member |
| PATCH /api/household/members/{id} | account holder | Edit member (own household only) |
| DELETE /api/household/members/{id} | account holder | Remove member if unreferenced and not the last account holder |
| POST /api/household/members/{id}/account | account holder | Give the member a login |
| GET /api/events | logged in | Read only event list for filters (Person 3 adds create and edit later) |
| GET /api/notices?scope=mine or all&event=&zone= | household | Notices, newest first |
| GET /api/notices/{id} | household | Title, message, event, zones, publication time |
| GET /api/auth/csrf | anyone | Sets the CSRF cookie when the app starts |
| GET /api/health | anyone (dev) | Database connection check |

## 5. Status

All ten Person 1 items are written, backend and frontend. See section 8 for what was tested.

## 6. Shared interfaces to agree with Persons 2 and 3

| # | Decision | My proposal |
|---|---|---|
| 1 | Current-user shape | `{ role: "household" or "staff", member_id, staff_id, household_id }` returned by `/api/auth/me`. Backend helper `get_current_user(request)` |
| 2 | Access checks | `@login_required_api`, `@household_required` (loads own household), `@staff_required` |
| 3 | Route names | Registration flow opens at `/shelter/register?event=<event_id>` (Person 2 confirms) |
| 4 | Which events accept registration | Only events with status `Active`. Not in the requirements, so the team must confirm |
| 5 | Status values | schema-v1 does not fix them. Proposal (from Report 3): event Active/Closed, registration Active/Cancelled, placement Reserved/Arrived/Departed/Transferred/Cancelled, shelter Open/Closed |
| 6 | Schema ownership | Django does not migrate our tables. Schema changes go into a new `backend/sql/schema-v*.sql` agreed by the team |
| 7 | Sessions and CSRF | Signed cookie sessions, CSRF header `X-CSRFToken` on all POST, PATCH, DELETE |
| 8 | `/api/events` | Person 1 provides GET only for now. Person 3 may extend it |

## 7. Points for the team to decide

1. **Seed passwords.** `seed-v1.sql` has placeholder hashes. Run `python manage.py set_demo_passwords` after loading it.
2. **Same email for staff and household.** Login checks STAFF first. Signup rejects an email that already exists in STAFF.
3. **"Referenced" member.** A member cannot be removed if they are in REGISTRATION_MEMBER or are a REGISTRATION.submitter_id. schema-v1 also blocks this with its RESTRICT foreign keys.
4. **Field rules not given** (postal code format, phone format, password length). The code uses basic validation and a minimum password length of 8.
5. **Time zone.** Django keeps `USE_TZ = True` and `TIME_ZONE = "UTC"` from the skeleton, so DATETIME values are read as UTC. The seed times were written as local times. Decide together how times are stored and shown.
6. **Router.** The frontend uses a small built-in router instead of adding react-router-dom, so `package-lock.json` did not change and `npm ci` still works. It uses the same names, so switching later only changes imports.
7. **Template files removed.** `App.css` and the three Vite template images were deleted because nothing uses them now.

## 8. What was and was not tested

| Item | Result |
|---|---|
| `schema-v1.sql` + `seed-v1.sql` load together, 13 tables, no foreign key problems | Tested in SQLite after a syntax-only translation. Not run in MySQL yet |
| Validation rules (`accounts/serializers.py`) | Tested, pure Python |
| Raw SQL used by the views | Tested against the seed data in SQLite |
| React pages and the built-in router: login, sign up, My Household (edit, add, enable login, remove), Notices (filters, details, register button), staff login, redirects, phone width | Tested in a real browser, 24 checks passed, against a mock API that copies the Django contract |
| Django itself: MySQL connection, models, sessions, CSRF, all endpoints, the 30 Django tests | **Not run.** Run `python manage.py test` |
| `npm ci`, `npm run build` (TypeScript check), `npm run lint`, Vite with the React Compiler | **Not run.** |

## 9. Assumptions made in the code (please confirm)

1. Password needs at least 8 characters. No format rule for postal code or phone.
2. A logged-in account holder cannot remove their own member row.
3. `can_register` is true only when the event status is `Active`.
4. Staff may read notices and events through the same read-only endpoints.
