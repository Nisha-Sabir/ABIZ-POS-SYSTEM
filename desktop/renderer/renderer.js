const state = {
  cart: [],
  products: []
};

const $ = (id) => document.getElementById(id);

function money(value) {
  return Number(value || 0).toFixed(2);
}

function setStatus(message, ok = true) {
  $('status').textContent = message;
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
    : '<p class="empty">No local products. Click Sync Products when internet is available.</p>';
}

async function refreshProducts() {
  state.products = await window.abiz.listProducts();
  renderProducts();
}

async function getBackendConfig() {
  return {
    baseUrl: await window.abiz.getSetting('backend_url'),
    token: await window.abiz.getSetting('auth_token')
  };
}

async function api(path, options = {}) {
  const { baseUrl, token } = await getBackendConfig();
  if (!baseUrl || !token) throw new Error('Backend URL/token missing in settings.');
  const response = await fetch(baseUrl.replace(/\/$/, '') + path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(options.headers || {})
    }
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || 'Server request failed.');
  }
  return response.status === 204 ? null : response.json();
}

async function scanProduct(code) {
  const product = await window.abiz.findProductByCode(code);
  if (!product) {
    $('product-result').textContent = 'Product not found in local database.';
    setStatus('Product not found. Sync products or add item online first.', false);
    return;
  }
  const existing = state.cart.find((item) => item.id === product.id);
  if (existing) existing.quantity += 1;
  else state.cart.push({ ...product, quantity: 1 });
  $('product-result').textContent = `${product.name} added. Price: ${money(product.sale_price)}`;
  renderCart();
  setStatus('Item added from USB scanner.');
}

async function syncProducts() {
  const products = await api('/products?limit=100');
  await window.abiz.upsertProducts(products);
  await refreshProducts();
  setStatus('Products synced for offline use.');
}

async function syncSales() {
  const pending = await window.abiz.getPendingSales();
  if (!pending.length) {
    setStatus('No pending offline sales.');
    return;
  }
  const response = await api('/sales/sync/offline', {
    method: 'POST',
    body: JSON.stringify({ sales: pending })
  });
  const syncedIds = response.results
    .filter((item) => item.status === 'synced' || item.status === 'already_synced')
    .map((item) => item.client_sale_id);
  await window.abiz.markSalesSynced(syncedIds);
  setStatus(`${syncedIds.length} offline sales synced.`);
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
    setStatus('Cart is empty.', false);
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
  await window.abiz.saveOfflineSale(sale);
  printInvoice(sale);
  state.cart = [];
  renderCart();
  setStatus('Sale saved locally. It will sync when internet is available.');
}

async function loadSettings() {
  $('backend-url').value = await window.abiz.getSetting('backend_url');
  $('auth-token').value = await window.abiz.getSetting('auth_token');
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
  $('save-settings').addEventListener('click', async () => {
    await window.abiz.setSetting('backend_url', $('backend-url').value.trim());
    await window.abiz.setSetting('auth_token', $('auth-token').value.trim());
    setStatus('Settings saved.');
  });
  await refreshProducts();
  renderCart();
});
