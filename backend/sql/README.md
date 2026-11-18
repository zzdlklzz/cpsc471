# Database setup

`schema-v1.sql` creates the project tables. `seed-v1.sql` adds made-up sample data.
Django migrations do not create these tables.

## First-time setup

1. Create an empty database (use the same name as `DB_NAME` in `backend/.env`):

   ```sql
   CREATE DATABASE evacbridge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

2. Load the schema, then the sample data:

   ```bash
   mysql -u root -p evacbridge < backend/sql/schema-v1.sql
   mysql -u root -p evacbridge < backend/sql/seed-v1.sql
   ```

   In MySQL Workbench: run `USE evacbridge;` first, then open and run each file.

3. Give the demo accounts a real password (the seed file only has placeholder hashes):

   ```bash
   cd backend
   python manage.py set_demo_passwords
   ```

   Every seeded account then uses the password in `DEMO_PASSWORD` (see `backend/.env.example`).

4. Check that Django sees the tables:

   ```bash
   python manage.py check_schema
   ```

## Demo logins

| Role | Email |
|---|---|
| Household | `anh.nguyen@household.example` |
| Household | `chidi.okafor@household.example` |
| Staff | `maria.chen@evacbridge.example` |

## Notes

- Run `schema-v1.sql` once on an empty database. It is not a reset script.
- Status values are not fixed by the schema. The seed data uses: event `Active` / `Closed`,
  registration `Active`, placement `Reserved` / `Arrived` / `Departed` / `Transferred`,
  shelter `Open` / `Closed`. The team should confirm these.
- Foreign keys use the default RESTRICT rule, so referenced rows cannot be deleted.
