# PostgreSQL Setup For ABIZ POS

Use one of these options when you are ready to connect the project to a database.

## Option 1: Docker Desktop

From the project folder:

```bash
docker compose up -d
```

Then run migrations:

```bash
alembic upgrade head
```

Default connection:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/abiz_pos
```

## Option 2: PostgreSQL Installer

1. Install PostgreSQL for Windows.
2. Keep port `5432`.
3. Create database named `abiz_pos`.
4. Put your password in `.env`.

Example:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/abiz_pos
```

Then run:

```bash
alembic upgrade head
```

## Verify

Start the app:

```bash
uvicorn main:app --reload
```

Open:

```text
http://127.0.0.1:8000/
```

Create the first account from the Register tab and choose `Super Admin`.
