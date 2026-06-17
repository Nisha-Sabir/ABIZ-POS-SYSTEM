const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const Database = require('better-sqlite3');

let db;

function openDatabase() {
  const dbPath = path.join(app.getPath('userData'), 'abiz-pos.sqlite');
  db = new Database(dbPath);
  db.pragma('journal_mode = WAL');
  db.exec(`
    CREATE TABLE IF NOT EXISTS settings (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS products (
      id INTEGER PRIMARY KEY,
      name TEXT NOT NULL,
      qr_code TEXT NOT NULL UNIQUE,
      purchase_price REAL NOT NULL,
      sale_price REAL NOT NULL,
      stock_quantity INTEGER NOT NULL DEFAULT 0,
      updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS offline_sales (
      client_sale_id TEXT PRIMARY KEY,
      payload TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'pending',
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      synced_at TEXT
    );
  `);
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 760,
    minWidth: 980,
    minHeight: 640,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js')
    }
  });

  win.loadFile(path.join(__dirname, 'renderer', 'index.html'));
}

app.whenReady().then(() => {
  openDatabase();
  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

ipcMain.handle('settings:get', (_event, key) => {
  const row = db.prepare('SELECT value FROM settings WHERE key = ?').get(key);
  return row?.value || '';
});

ipcMain.handle('settings:set', (_event, key, value) => {
  db.prepare(`
    INSERT INTO settings (key, value) VALUES (?, ?)
    ON CONFLICT(key) DO UPDATE SET value = excluded.value
  `).run(key, value);
  return true;
});

ipcMain.handle('products:upsertMany', (_event, products) => {
  const insert = db.prepare(`
    INSERT INTO products (id, name, qr_code, purchase_price, sale_price, stock_quantity, updated_at)
    VALUES (@id, @name, @qr_code, @purchase_price, @sale_price, @stock_quantity, CURRENT_TIMESTAMP)
    ON CONFLICT(id) DO UPDATE SET
      name = excluded.name,
      qr_code = excluded.qr_code,
      purchase_price = excluded.purchase_price,
      sale_price = excluded.sale_price,
      stock_quantity = excluded.stock_quantity,
      updated_at = CURRENT_TIMESTAMP
  `);
  const tx = db.transaction((items) => items.forEach((item) => insert.run(item)));
  tx(products);
  return true;
});

ipcMain.handle('products:findByCode', (_event, code) => {
  return db.prepare('SELECT * FROM products WHERE qr_code = ?').get(code);
});

ipcMain.handle('products:list', () => {
  return db.prepare('SELECT * FROM products ORDER BY name').all();
});

ipcMain.handle('sales:saveOffline', (_event, sale) => {
  db.prepare(`
    INSERT INTO offline_sales (client_sale_id, payload, status)
    VALUES (?, ?, 'pending')
  `).run(sale.client_sale_id, JSON.stringify(sale));
  return true;
});

ipcMain.handle('sales:pending', () => {
  return db.prepare("SELECT * FROM offline_sales WHERE status = 'pending' ORDER BY created_at").all()
    .map((row) => JSON.parse(row.payload));
});

ipcMain.handle('sales:markSynced', (_event, ids) => {
  const stmt = db.prepare("UPDATE offline_sales SET status = 'synced', synced_at = CURRENT_TIMESTAMP WHERE client_sale_id = ?");
  const tx = db.transaction((items) => items.forEach((id) => stmt.run(id)));
  tx(ids);
  return true;
});
