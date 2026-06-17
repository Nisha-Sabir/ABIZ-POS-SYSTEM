# ABIZ Global Services POS System

Professional FastAPI backend for the ABIZ Global Services POS System.

## Current Scope

Current scope includes project setup, PostgreSQL configuration, Alembic migration wiring, SQLAlchemy models, JWT authentication, product/category management, inventory management, QR code workflow, sales checkout, Digi Khata, license keys, a connected frontend, and a desktop/offline foundation.

Advanced reports and Android APK packaging are not included yet.

## Tech Stack

- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Pydantic Settings
- JWT Authentication
- Passlib bcrypt password hashing

## Project Structure

```text
app/
  api/
  core/
  database/
  models/
  schemas/
  services/
  utils/
alembic/
  versions/
main.py
requirements.txt
.env.example
docker-compose.yml
frontend/
desktop/
README.md
```

## Setup

1. Create and activate a virtual environment.

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Create a local environment file.

```bash
copy .env.example .env
```

4. Update `DATABASE_URL` in `.env` with your PostgreSQL credentials.

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/abiz_pos
SECRET_KEY=replace-this-with-a-long-random-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALGORITHM=HS256
```

5. Create the PostgreSQL database if it does not already exist.

```sql
CREATE DATABASE abiz_pos;
```

PostgreSQL setup details are also available in `POSTGRESQL_SETUP.md`.

## Alembic Migrations

Apply migrations:

```bash
alembic upgrade head
```

## Run the Application

```bash
uvicorn main:app --reload
```

Open:

- Frontend app: http://127.0.0.1:8000/
- API docs: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

## Railway Deployment

Railway uses `railway.json`.

Required variables:

```env
DATABASE_URL=your_railway_postgres_url
SECRET_KEY=your_strong_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALGORITHM=HS256
ENVIRONMENT=production
DEBUG=false
```

Start command:

```bash
alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Desktop Offline Client

The `desktop/` folder contains an Electron-based offline POS foundation.

- Railway hosts the central backend and owner web dashboard.
- The desktop app runs on the shopkeeper's Windows PC.
- IndexedDB local database saves offline sales on the client computer.
- USB QR/barcode scanners work as keyboard input in the scanner field.
- Pending offline sales sync to `POST /api/v1/sales/sync/offline` when internet is available.

Run desktop app:

```bash
cd desktop
npm install
npm start
```

Build Windows installer:

```bash
npm run build
```

Portable desktop package created locally:

```text
desktop/release/ABIZ-POS-Desktop.zip
```

Extract the ZIP and run `ABIZ POS.exe`.

See `DESKTOP_OFFLINE_PLAN.md` for the offline workflow and remaining production steps.

## Authentication

Available authentication routes:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

Register the first super admin:

```json
{
  "full_name": "Super Admin",
  "email": "admin@example.com",
  "password": "StrongPass123",
  "role": "super_admin"
}
```

After the first user exists, public registration can create `admin` users only.

Login request:

```json
{
  "email": "admin@example.com",
  "password": "StrongPass123"
}
```

Login response:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

Use the returned token in protected requests:

```http
Authorization: Bearer jwt-token
```

Reusable authentication dependencies:

- `get_current_user()`
- `get_current_admin()`
- `get_current_super_admin()`

## Product Management

All product and category routes require a valid JWT bearer token. Only `admin` and `super_admin` users can access them.

Category routes:

- `POST /api/v1/categories`
- `GET /api/v1/categories?skip=0&limit=100`
- `PUT /api/v1/categories/{category_id}`
- `DELETE /api/v1/categories/{category_id}`

Product routes:

- `POST /api/v1/products`
- `GET /api/v1/products?skip=0&limit=100`
- `GET /api/v1/products?search=milk`
- `GET /api/v1/products?category_id=1`
- `GET /api/v1/products/qr/{qr_code}`
- `GET /api/v1/products/{product_id}`
- `POST /api/v1/products/{product_id}/qr`
- `POST /api/v1/products/{product_id}/qr/regenerate`
- `PUT /api/v1/products/{product_id}`
- `DELETE /api/v1/products/{product_id}`

Create category request:

```json
{
  "name": "Beverages",
  "description": "Cold drinks, juices, and water"
}
```

If `qr_code` is omitted during product creation, the backend auto-generates a unique product QR code.

Create product request:

```json
{
  "name": "Mineral Water 500ml",
  "qr_code": "ABIZ-0001",
  "purchase_price": 40,
  "sale_price": 50,
  "stock_quantity": 100,
  "category_id": 1
}
```

## Inventory Management

All inventory routes require a valid JWT bearer token. Only `admin` and `super_admin` users can access them.

Inventory routes:

- `POST /api/v1/inventory/products/{product_id}/stock-in`
- `POST /api/v1/inventory/products/{product_id}/stock-out`
- `GET /api/v1/inventory/products/{product_id}/stock`
- `GET /api/v1/inventory/history?skip=0&limit=100`
- `GET /api/v1/inventory/history?search=water`
- `GET /api/v1/inventory/history?product_id=1`
- `GET /api/v1/inventory/history?start_date=2026-06-01&end_date=2026-06-13`
- `GET /api/v1/inventory/low-stock?threshold=10`

Stock in request:

```json
{
  "quantity": 25,
  "notes": "Supplier delivery"
}
```

Stock out request:

```json
{
  "quantity": 5,
  "notes": "Damaged items removed"
}
```

Stock out is rejected when the requested quantity is greater than the current product stock.

## QR Code And Sales Cart Foundation

All QR and cart routes require a valid JWT bearer token.

QR product routes:

- `POST /api/v1/products/{product_id}/qr`
- `GET /api/v1/products/qr/{qr_code}`
- `POST /api/v1/products/{product_id}/qr/regenerate`

Sales foundation routes:

- `GET /api/v1/sales/scan/{qr_code}`
- `POST /api/v1/sales/cart/items`
- `GET /api/v1/sales/cart`
- `DELETE /api/v1/sales/cart/items/{product_id}`
- `POST /api/v1/sales/checkout`
- `GET /api/v1/sales`
- `GET /api/v1/sales/{sale_id}`

Scan response includes product name, sale price, and available stock.

Add to cart request:

```json
{
  "qr_code": "ABIZ-PROD-123456789ABC",
  "quantity": 2
}
```

The cart validates available stock before adding items. Cart totals include item profit and total profit using:

```text
sale_price - purchase_price
```

## Digi Khata

Digi Khata is updated automatically after checkout.

- `GET /api/v1/digi-khata`

It returns daily total sales and total profit.

## Super Admin License Keys

Only `super_admin` users can manage license keys.

- `POST /api/v1/license-keys`
- `GET /api/v1/license-keys`
- `POST /api/v1/license-keys/{license_id}/assign`
- `POST /api/v1/license-keys/{license_id}/revoke`

## Database Models

- User
- Category
- Product
- CartItem
- InventoryTransaction
- Sale
- SaleItem
- DigiKhata
- LicenseKey

Relationships:

- A sale has many sale items.
- A sale item belongs to one sale.
- A sale item belongs to one product.
- A product can appear in many sale items.
