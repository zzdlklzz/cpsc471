# EvacBridge

CPSC 471 project using React + TypeScript (Vite) and Python + Django.

## Requirements

- Node.js 22.12 or newer in the Node 22 release line, with npm
- Python 3.13 (the version used for the current backend setup)
- Git

The frontend and backend currently run independently. MySQL integration is not
configured yet; Django still uses its default local SQLite configuration. No
MySQL installation or environment file is required to run this skeleton.

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
skeleton. You can leave them unapplied for now; the project tables are not yet
implemented.

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
