# ABIZ Global Services POS Testing Report

## Environment

- Backend: FastAPI
- Database: PostgreSQL `abiz_pos`
- Frontend: Served from FastAPI at `/`

## Verified On 2026-06-16

Passed:

- PostgreSQL connection
- Alembic migrations
- Frontend page load
- API docs load
- User registration
- User login
- JWT current user
- Category create
- Product create with auto QR code
- Stock in
- QR product scan
- Cart add
- Cart total calculation
- Checkout
- Stock reduction after sale
- Sale profit calculation
- Digi Khata daily sales/profit update
- Super Admin license key generation
- Super Admin license key revocation
- Frontend JavaScript syntax check
- Backend Python compile check

## Smoke Test Result

```json
{
  "stock_after_add": 5,
  "scan_price": "150.00",
  "cart_total": "300.00",
  "sale_total": "300.00",
  "sale_profit": "100.00",
  "digi_khata_entries": 1,
  "license_key_status_after_revoke": "revoked"
}
```

## Notes

- Camera QR scanning is implemented using the browser `BarcodeDetector` API.
- If a browser or WebView does not support camera barcode scanning, manual QR entry remains available.
- For public hosting, camera access requires HTTPS. Localhost and APK WebView can use camera permissions.
