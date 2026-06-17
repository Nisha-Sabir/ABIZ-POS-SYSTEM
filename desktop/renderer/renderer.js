const state = {
  cart: [],
  products: []
};

const $ = (id) => document.getElementById(id);

const localDb = (() => {
  const request = indexedDB.open('abiz-pos-local-db', 1);
  const ready = new Promise((resolve, reject) => {
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains('settings')) db.createObjectStore('settings');
      if (!db.objectStoreNames.contains('products')) db.createObjectStore('products', { keyPath: 'id' });
      if (!db.objectStoreNames.contains('pending_sales')) db.createObjectStore('pending_sales', { keyPath: 'client_sale_id' });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });

  async function store(name, mode = 'readonly') {
    const db = await ready;
    return db.transaction(name, mode).objectStore(name);
  }

  return {
    async getSetting(key) {
      const objectStore = await store('settings');
      return new Promise((resolve) => {
        const req = objectStore.get(key);
        req.onsuccess = () => resolve(req.result || '');
        req.onerror = () => resolve('');
      });
    },
    async setSetting(key, value) {
      const objectStore = await store('settings', 'readwrite');
      return new Promise((resolve, reject) => {
        const req = objectStore.put(value, key);
        req.onsuccess = () => resolve(true);
        req.onerror = () => reject(req.error);
      });
    },
    async putProducts(products) {
      const objectStore = await store('products', 'readwrite');
      return Promise.all(products.map((product) => new Promise((resolve, reject) => {
        const req = objectStore.put(product);
        req.onsuccess = resolve;
        req.onerror = () => reject(req.error);
      })));
    },
    async listProducts() {
      const objectStore = await store('products');
      return new Promise((resolve) => {
        const req = objectStore.getAll();
        req.onsuccess = () => resolve(req.result || []);
        req.onerror = () => resolve([]);
      });
    },
    async addPendingSale(sale) {
      const objectStore = await store('pending_sales', 'readwrite');
      return new Promise((resolve, reject) => {
        const req = objectStore.put(sale);
        req.onsuccess = () => resolve(true);
        req.onerror = () => reject(req.error);
      });
    },
    async listPendingSales() {
      const objectStore = await store('pending_sales');
      return new Promise((resolve) => {
        const req = objectStore.getAll();
        req.onsuccess = () => resolve(req.result || []);
        req.onerror = () => resolve([]);
      });
    },
    async removePendingSales(ids) {
      const objectStore = await store('pending_sales', 'readwrite');
      return Promise.all(ids.map((id) => new Promise((resolve, reject) => {
        const req = objectStore.delete(id);
        req.onsuccess = resolve;
        req.onerror = () => reject(req.error);
      })));
    }
  };
})();

function money(value) {
  return Number(value || 0).toFixed(2);
}

async function setStatus(message, ok = true) {
  const pending = await localDb.listPendingSales();
  $('status').textContent = `${navigator.onLine ? 'Online' : 'Offline'} | Pending: ${pending.length} | ${message}`;
  $('status').className = ok ? 'ok' : 'bad';
}

function renderCart() {
  $('cart-list').innerHTML = state.cart.length
    ? state.cart.map((item) => `
      <div class="cart-row">
        <div>
          <strong>${item.name}</strong>
          <small>${item.qr_code}</small>
        </div>
        <div>${item.quantity} x ${money(item.sale_price)}</div>
      </div>
    `).join('')
    : '<p class="empty">No items added.</p>';

  const total = state.cart.reduce((sum, item) => sum + item.sale_price * item.quantity, 0);
  $('total').textContent = money(total);
}

function renderProducts() {
  $('products-list').innerHTML = state.products.length
    ? state.products.map((product) => `
      <div class="product">
        <strong>${product.name}</strong>
        <span>${product.qr_code}</span>
        <b>Stock: ${product.stock_quantity}</b>
      </div>
    `).join('')
    : '<p class="empty">No local products. Login and click Sync Products when internet is available.</p>';
}

async function refreshProducts() {
  state.products = await localDb.listProducts();
  renderProducts();
}

async function getBackendConfig() {
  return {
    baseUrl: await localDb.getSetting('backend_url'),
    token: await localDb.getSetting('auth_token')
  };
}

async function api(path, options = {}) {
  const { baseUrl, token } = await getBackendConfig();
  if (!baseUrl) throw new Error('Backend URL missing in Settings.');
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(baseUrl.replace(/\/$/, '') + path, { ...options, headers });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || 'Server request failed.');
  }
  return response.status === 204 ? null : response.json();
}

async function login() {
  const email = $('login-email').value.trim();
  const password = $('login-password').value;
  if (!email || !password) throw new Error('Email and password required.');
  const token = await api('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  });
  await localDb.setSetting('auth_token', token.access_token);
  await syncProducts();
  await setStatus('Logged in and products synced.');
}

async function scanProduct(code) {
  const product = state.products.find((item) => item.qr_code === code);
  if (!product) {
    $('product-result').textContent = 'Product not found in local database.';
    await setStatus('Product not found. Sync products first.', false);
    return;
  }
  const existing = state.cart.find((item) => item.id === product.id);
  if (existing) existing.quantity += 1;
  else state.cart.push({ ...product, quantity: 1 });
  $('product-result').textContent = `${product.name} added. Price: ${money(product.sale_price)}`;
  renderCart();
  await setStatus('Item added from USB scanner.');
}

async function syncProducts() {
  const products = await api('/products?limit=100');
  await localDb.putProducts(products);
  await refreshProducts();
  await setStatus('Products synced for offline use.');
}

async function syncSales() {
  const pending = await localDb.listPendingSales();
  if (!pending.length) {
    await setStatus('No pending offline sales.');
    return;
  }
  const response = await api('/sales/sync/offline', {
    method: 'POST',
    body: JSON.stringify({ sales: pending })
  });
  const syncedIds = response.results
    .filter((item) => item.status === 'synced' || item.status === 'already_synced')
    .map((item) => item.client_sale_id);
  await localDb.removePendingSales(syncedIds);
  await setStatus(`${syncedIds.length} offline sales synced.`);
}

async function tryAutoSync() {
  if (!navigator.onLine) {
    await setStatus('Waiting for internet.');
    return;
  }
  try {
    await syncSales();
  } catch {
    await setStatus('Auto sync will retry.', false);
  }
}

function printInvoice(sale) {
  const invoice = window.open('', '_blank', 'width=420,height=640');
  invoice.document.write(`
    <html><head><title>Invoice</title><style>
      body{font-family:Arial,sans-serif;padding:16px}
      h1{font-size:18px;margin:0 0 8px}
      table{width:100%;border-collapse:collapse;margin-top:12px}
      td,th{border-bottom:1px solid #ddd;padding:6px;text-align:left}
      .total{font-size:18px;font-weight:bold;text-align:right;margin-top:16px}
    </style></head><body>
      <h1>ABIZ Global Services</h1>
      <div>Invoice: ${sale.client_sale_id}</div>
      <div>Date: ${new Date(sale.created_at).toLocaleString()}</div>
      <table><thead><tr><th>Item</th><th>Qty</th><th>Price</th></tr></thead><tbody>
      ${state.cart.map((item) => `<tr><td>${item.name}</td><td>${item.quantity}</td><td>${money(item.sale_price)}</td></tr>`).join('')}
      </tbody></table>
      <div class="total">Total: ${$('total').textContent}</div>
      <script>window.print();<\/script>
    </body></html>
  `);
  invoice.document.close();
}

async function checkout() {
  if (!state.cart.length) {
    await setStatus('Cart is empty.', false);
    return;
  }
  const sale = {
    client_sale_id: `DESK-${Date.now()}`,
    created_at: new Date().toISOString(),
    items: state.cart.map((item) => ({
      product_id: item.id,
      quantity: item.quantity,
      unit_price: item.sale_price
    }))
  };
  await localDb.addPendingSale(sale);
  printInvoice(sale);
  state.cart = [];
  renderCart();
  await setStatus('Sale saved locally. Auto sync will run when internet is available.');
  await tryAutoSync();
}

async function loadSettings() {
  $('backend-url').value = await localDb.getSetting('backend_url');
}

document.addEventListener('DOMContentLoaded', async () => {
  $('scanner-input').focus();
  $('scanner-input').addEventListener('keydown', async (event) => {
    if (event.key !== 'Enter') return;
    const code = event.target.value.trim();
    event.target.value = '';
    if (code) await scanProduct(code);
  });
  $('sync-products').addEventListener('click', () => syncProducts().catch((error) => setStatus(error.message, false)));
  $('sync-sales').addEventListener('click', () => syncSales().catch((error) => setStatus(error.message, false)));
  $('checkout').addEventListener('click', () => checkout().catch((error) => setStatus(error.message, false)));
  $('clear-cart').addEventListener('click', () => { state.cart = []; renderCart(); });
  $('settings-btn').addEventListener('click', async () => { await loadSettings(); $('settings-dialog').showModal(); });
  $('login-btn').addEventListener('click', () => $('login-dialog').showModal());
  $('save-settings').addEventListener('click', async () => {
    await localDb.setSetting('backend_url', $('backend-url').value.trim());
    await setStatus('Settings saved.');
  });
  $('do-login').addEventListener('click', () => login().catch((error) => setStatus(error.message, false)));
  window.addEventListener('online', tryAutoSync);
  window.addEventListener('offline', () => setStatus('Offline mode active.'));
  setInterval(tryAutoSync, 60000);
  await refreshProducts();
  renderCart();
  await setStatus('Desktop app ready.');
});
