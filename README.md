# EvacBridge

CPSC 471 project using React + TypeScript (Vite) and Python + Django.

## Requirements

- Node.js 22.12 or newer in the Node 22 release line, with npm
- Python 3.13 (the version used for the current backend setup)
- Git
- A running local MySQL Server and an existing project database

The frontend and backend currently run independently. Django is configured for
MySQL; each member supplies their own connection details in `backend/.env`.

## Clone the repository

```bash
git clone https://github.com/zzdlklzz/cpsc471.git
cd cpsc471
```

If you already have the repository, open a terminal in its root folder.

## Frontend

From the repository root:

```bash
cd frontend
npm ci
npm run dev
```

Open the URL printed by Vite, usually http://localhost:5173.

For subsequent runs, only `npm run dev` is needed. Run `npm ci` again when the
committed dependencies change.

Optional checks, from `frontend/`:

```bash
npm run build
npm run lint
```

## Backend

Open a second terminal at the repository root.

Before installing Python dependencies, ensure the MySQL client development
libraries are available for `mysqlclient`. On macOS with MySQL installed under
`/usr/local/mysql`, use:

```bash
brew install pkg-config
export PKG_CONFIG_PATH="/usr/local/mysql/lib/pkgconfig"
export MYSQLCLIENT_LDFLAGS="-L/usr/local/mysql/lib -lmysqlclient -Wl,-rpath,/usr/local/mysql/lib"
```

Other installations may use a different path. See the
[mysqlclient installation instructions](https://github.com/PyMySQL/mysqlclient#install)
for your platform.

Copy `backend/.env.example` to `backend/.env` if you do not already have one.
Fill in `DB_NAME`, `DB_USER`, and `DB_PASSWORD` using your existing database and
connection credentials. Adjust the host/port if needed. The database name is the
schema name, not the Workbench connection label. Do this before running any
`manage.py` commands. Do not commit `.env`.

### macOS / Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py check
python manage.py runserver
```

### Windows (PowerShell)

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver
```

Open http://127.0.0.1:8000 to see the Django starter page.

Django may warn about unapplied migrations. This is expected for the empty
skeleton. You can leave them unapplied for now. Initialize the project tables
using [the SQL setup instructions](backend/sql/README.md); Django migrations do
not load `backend/sql/schema.sql`.

For subsequent runs on macOS/Linux, from `backend/`:

```bash
source .venv/bin/activate
python manage.py runserver
```

On Windows, run `.\.venv\Scripts\python.exe manage.py runserver` instead.
Reinstall from `requirements.txt` when the committed Python dependencies change.

## Working locally

- Keep both terminals running to use both apps. Press `Ctrl+C` to stop either server.
- Each person creates their own virtual environment and installs dependencies locally.
- Do not commit `.venv/`, `node_modules/`, `dist/`, local `.env` files, or SQLite databases; Git ignores them.
- Commit dependency changes with `frontend/package-lock.json` and `backend/requirements.txt` as appropriate.

## Folders

```text
frontend/       React + TypeScript application
backend/        Django project and Python requirements
```
