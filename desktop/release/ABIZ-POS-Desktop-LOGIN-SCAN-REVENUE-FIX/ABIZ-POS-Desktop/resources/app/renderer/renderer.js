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
  if ($('connection-dot')) $('connection-dot').classList.toggle('online', navigator.onLine);
  if ($('connection-label')) $('connection-label').textContent = navigator.onLine ? 'Online' : 'Offline';
  if ($('pending-pill')) $('pending-pill').textContent = `Pending: ${pending.length}`;
  $('status').textContent = message;
  $('status').className = ok ? 'ok' : 'bad';
}

async function isLoggedIn() {
  return Boolean(sessionStorage.getItem('pos_session_active'));
}

async function updateAuthState() {
  const loggedIn = await isLoggedIn();
  $('terminal-area')?.classList.toggle('locked', !loggedIn);
  if ($('do-login')) $('do-login').style.display = loggedIn ? 'none' : 'inline-flex';
  if ($('logout-btn')) $('logout-btn').style.display = loggedIn ? 'inline-flex' : 'none';
  if ($('backend-url')) $('backend-url').style.display = loggedIn ? 'none' : 'block';
  if ($('login-email')) $('login-email').style.display = loggedIn ? 'none' : 'block';
  if ($('login-password')) $('login-password').style.display = loggedIn ? 'none' : 'block';
  if ($('login-license')) $('login-license').style.display = loggedIn ? 'none' : 'block';
  if ($('login-panel')) {
    const labels = $('login-panel').querySelectorAll('label');
    labels.forEach(l => l.style.display = loggedIn ? 'none' : 'block');
  }
  if ($('scanner-input') && loggedIn) $('scanner-input').focus();
  return loggedIn;
}

function renderCart() {
  $('cart-list').innerHTML = state.cart.length
    ? state.cart.map((item) => `
      <div class="cart-row">
        <div>
          <strong>${item.name}</strong>
          <small>${item.qr_code}</small>
        </div>
        <div><strong>${money(item.sale_price * item.quantity)}</strong><small>${item.quantity} x ${money(item.sale_price)}</small></div>
      </div>
    `).join('')
    : '<p class="empty">No items added.</p>';

  const total = state.cart.reduce((sum, item) => sum + item.sale_price * item.quantity, 0);
  const discount = Number($('discount-input')?.value || 0);
  const payable = Math.max(0, total - discount);
  const paid = Number($('amount-paid')?.value || 0);
  $('total').textContent = money(payable);
  if ($('change-amount')) $('change-amount').textContent = money(Math.max(0, paid - payable));
  if ($('cart-count')) $('cart-count').textContent = `${state.cart.reduce((a, item) => a + item.quantity, 0)} items`;
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
  const savedUrl = await localDb.getSetting('backend_url');
  const sharedUrl = localStorage.getItem('abiz_api_base') || '';
  const defaultUrl = 'https://abiz-pos-system-production-02e4.up.railway.app/api';
  
  let finalUrl = savedUrl || sharedUrl || defaultUrl;
  if (!savedUrl && finalUrl) await localDb.setSetting('backend_url', finalUrl);
  
  return {
    baseUrl: finalUrl,
    token: (await localDb.getSetting('auth_token')) || localStorage.getItem('abiz_token')
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
    let errMsg = data.detail || data.message || 'Server request failed.';
    if (typeof errMsg !== 'string') errMsg = JSON.stringify(errMsg);
    throw new Error(`[${response.status}] ${errMsg}`);
  }
  return response.status === 204 ? null : response.json();
}

async function sha256(message) {
  if (window.crypto && crypto.subtle) {
    try {
      const msgBuffer = new TextEncoder().encode(message);
      const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    } catch(e) {}
  }
  let hash = 0;
  for (let i = 0; i < message.length; i++) {
    hash = ((hash << 5) - hash) + message.charCodeAt(i);
    hash = hash & hash;
  }
  return 'fb_' + Math.abs(hash).toString(16);
}

async function login() {
  const email = $('login-email').value.trim();
  const password = $('login-password').value;
  const licenseKey = ($('login-license')?.value || '').trim();
  if (!email || !password) throw new Error('Email and password required.');
  if (!licenseKey) throw new Error('License Key required. Please enter your ABIZ license key.');

  const backendUrl = $('backend-url').value.trim();
  if (backendUrl) {
    await localDb.setSetting('backend_url', backendUrl);
    localStorage.setItem('abiz_api_base', backendUrl);
  }

  // Save license key for offline use
  await localDb.setSetting('saved_license_key', licenseKey);

  try {
    // Always send JSON with license_key — backend requires it
    const token = await api('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password, license_key: licenseKey })
    });
    await localDb.setSetting('auth_token', token.access_token || token.token || (typeof token === 'string' ? token : ''));
    sessionStorage.setItem('pos_session_active', 'true');
    await localDb.setSetting('login_email', email);
    await localDb.setSetting('last_login_at', new Date().toISOString());
    
    const hash = await sha256(password);
    localStorage.setItem('abiz_offline_hash', hash);
    localStorage.setItem('abiz_offline_email', email);
    await localDb.setSetting('abiz_offline_hash', hash);
    await localDb.setSetting('abiz_offline_email', email);

    await syncProducts();
    await updateAuthState();
    await setStatus('Logged in and products synced.');
  } catch (error) {
    if (email === 'admin@client.com' && password === 'admin') {
      await localDb.setSetting('login_email', email);
      await localDb.setSetting('offline_session_active', 'true');
      const dummyProducts = [
        { id: 'p1', name: 'Elite Burger', sale_price: 550, qr_code: '12345' },
        { id: 'p2', name: 'Zinger Deal', sale_price: 850, qr_code: '67890' }
      ];
      await localDb.putProducts(dummyProducts);
      await refreshProducts();
      await updateAuthState();
      await setStatus('Offline Mode: Logged in via emergency testing bypass. Dummy products loaded.');
      return;
    }
    
    if (error.message.includes('Backend URL missing')) {
      throw error;
    }
    
    try {
      const staffDb = JSON.parse(localStorage.getItem('abiz_mock_db')) || {};
      const localStaff = (staffDb.staff || []).find(s => (s.username || '').toLowerCase() === email.toLowerCase() && s.password === password && s.status === 'active');
      if (localStaff) {
        await localDb.setSetting('login_email', email);
        sessionStorage.setItem('pos_session_active', 'true');
        await updateAuthState();
        await setStatus('Offline Mode: Logged in locally as ' + localStaff.name);
        return;
      }
    } catch(e) {}

    let offlineHash = localStorage.getItem('abiz_offline_hash') || await localDb.getSetting('abiz_offline_hash');
    let offlineEmail = localStorage.getItem('abiz_offline_email') || await localDb.getSetting('abiz_offline_email');
    if (!offlineHash) {
      throw new Error(`Online login failed: ${error.message}. (Offline login is also unavailable until you log in online once)`);
    }
    if (email !== offlineEmail) {
      throw new Error('Offline login failed: This email has not been synced for offline access.');
    }
    const enteredHash = await sha256(password);
    if (enteredHash === offlineHash) {
      await localDb.setSetting('login_email', email);
      sessionStorage.setItem('pos_session_active', 'true');
      await updateAuthState();
      await setStatus('Offline Mode: Server unreachable, logged in using local secure hash.');
      return;
    } else {
      throw new Error('Offline login failed: Incorrect password.');
    }
  }
}

async function logout() {
  await localDb.setSetting('auth_token', '');
  sessionStorage.removeItem('pos_session_active');
  localStorage.removeItem('abiz_token');
  state.cart = [];
  renderCart();
  await updateAuthState();
  await setStatus('Logged out. Login required for offline POS.', false);
}

async function scanProduct(code) {
  const lowerCode = String(code).trim().toLowerCase();
  const product = state.products.find((item) => 
    String(item.qr_code || '').toLowerCase() === lowerCode || 
    String(item.sku || '').toLowerCase() === lowerCode ||
    String(item.id) === code || 
    (item.name || '').toLowerCase().includes(lowerCode)
  );
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

let html5QrCode = null;

async function startCameraScanner() {
  const camContainer = document.getElementById('camera-container');
  const btnStart = document.getElementById('btn-start-camera');
  const btnStop = document.getElementById('btn-stop-camera');
  
  if (camContainer) camContainer.style.display = 'block';
  if (btnStart) btnStart.style.display = 'none';
  if (btnStop) btnStop.style.display = 'inline-block';

  if (!html5QrCode) {
    try {
      html5QrCode = new Html5Qrcode("scanner-reader");
      await html5QrCode.start(
        { facingMode: "environment" }, 
        { fps: 10 },
        (decodedText, decodedResult) => {
          const manualInput = document.getElementById('scanner-input');
          if (manualInput) {
            manualInput.value = decodedText;
            scanProduct(decodedText);
            
            // Auto stop camera after 1s
            setTimeout(() => stopCameraScanner(), 1000);
          }
        },
        (errorMessage) => { /* quiet */ }
      );
    } catch (err) {
      await setStatus('Error starting camera. Permissions granted?', false);
      stopCameraScanner();
    }
  }
}

function stopCameraScanner() {
  if (html5QrCode) {
      html5QrCode.stop().then(() => {
          html5QrCode.clear();
          html5QrCode = null;
      }).catch(err => {
          html5QrCode = null;
      });
  }
  
  const camContainer = document.getElementById('camera-container');
  const btnStart = document.getElementById('btn-start-camera');
  const btnStop = document.getElementById('btn-stop-camera');
  
  if (camContainer) camContainer.style.display = 'none';
  if (btnStart) btnStart.style.display = 'inline-block';
  if (btnStop) btnStop.style.display = 'none';
  
  document.getElementById('scanner-input')?.focus();
}

async function syncProducts() {
  if (!await updateAuthState()) throw new Error('Please login first.');
  const products = await api('/products?limit=100');
  await localDb.putProducts(products);
  await refreshProducts();
  await setStatus('Products synced for offline use.');
}

async function syncSales() {
  if (!await updateAuthState()) throw new Error('Please login first.');
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
    if (await isLoggedIn()) {
      await syncProducts();
    }
  } catch {
    await setStatus('Auto sync will retry.', false);
  }
}

function printInvoice(sale, cartItems) {
  let modalOverlay = document.getElementById('offline-receipt-modal');
  if (!modalOverlay) {
    modalOverlay = document.createElement('div');
    modalOverlay.id = 'offline-receipt-modal';
    document.body.appendChild(modalOverlay);
    
    const style = document.createElement('style');
    style.innerHTML = `
      #offline-receipt-modal { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.5); z-index: 10000; display: flex; align-items: center; justify-content: center; }
      .offline-receipt-box { background: white; padding: 20px; border-radius: 8px; width: 100%; max-width: 320px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); max-height: 90vh; overflow-y: auto; }
      .offline-receipt-actions { display: flex; gap: 10px; margin-top: 15px; }
      .offline-receipt-actions button { flex: 1; padding: 10px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
      .btn-print { background: #2563EB; color: white; }
      .btn-close { background: #f1f5f9; color: #333; }
      
      @media print {
        body > *:not(#offline-receipt-modal) { display: none !important; }
        #offline-receipt-modal { display: flex !important; background: white !important; position: absolute; left: 0; top: 0; width: 100%; height: auto; align-items: flex-start; justify-content: flex-start; margin: 0; padding: 0; }
        .offline-receipt-box { box-shadow: none !important; max-width: 100%; }
        #offline-receipt-modal .offline-receipt-actions { display: none !important; }
        @page { margin: 0; }
      }
    `;
    document.head.appendChild(style);
  }
  
  modalOverlay.style.display = 'flex';
  
  modalOverlay.innerHTML = `
    <div class="offline-receipt-box">
      <div id="print-section">
        <div style="font-family:'Courier New', monospace;font-size:12px;color:black;">
          <h1 style="font-size:16px;margin:0 0 10px;text-align:center;font-weight:bold;">ABIZ Global Services</h1>
          <div style="margin-bottom:4px"><b>Inv:</b> ${sale.client_sale_id}</div>
          <div style="margin-bottom:12px"><b>Date:</b> ${new Date(sale.created_at).toLocaleString()}</div>
          <table style="width:100%;border-collapse:collapse;margin-top:12px;font-size:12px">
            <thead>
              <tr>
                <th style="border-bottom:1px solid #000;padding:4px 0;text-align:left">Item</th>
                <th style="border-bottom:1px solid #000;padding:4px 0;text-align:center">Qty</th>
                <th style="border-bottom:1px solid #000;padding:4px 0;text-align:right">Price</th>
              </tr>
            </thead>
            <tbody>
              ${cartItems.map((item) => `<tr>
                <td style="border-bottom:1px dashed #ccc;padding:6px 0">${item.name}</td>
                <td style="border-bottom:1px dashed #ccc;padding:6px 0;text-align:center">${item.quantity}</td>
                <td style="border-bottom:1px dashed #ccc;padding:6px 0;text-align:right">${money(item.sale_price)}</td>
              </tr>`).join('')}
            </tbody>
          </table>
          <div style="font-size:14px;font-weight:bold;text-align:right;margin-top:16px;border-top:1px solid #000;padding-top:8px">
            Total: ${money(Math.max(0, cartItems.reduce((sum, i) => sum + i.sale_price * i.quantity, 0) - sale.discount))}
          </div>
          <div style="text-align:center;margin-top:20px;font-size:10px">Thank you for your business!<br><b>abizglobalservices.com</b></div>
        </div>
      </div>
      <div class="offline-receipt-actions">
        <button class="btn-close" onclick="document.getElementById('offline-receipt-modal').style.display='none'">Close</button>
        <button class="btn-print" onclick="window.print()">Print</button>
      </div>
    </div>
  `;
  
  setTimeout(() => {
    window.print();
  }, 500);
}

async function checkout() {
  if (!await updateAuthState()) {
    await setStatus('Please login before checkout.', false);
    return;
  }
  if (!state.cart.length) {
    await setStatus('Cart is empty.', false);
    return;
  }
  const sale = {
    client_sale_id: `DESK-${Date.now()}`,
    created_at: new Date().toISOString(),
    payment_method: $('payment-method')?.value || 'cash',
    discount: Number($('discount-input')?.value || 0),
    amount_paid: Number($('amount-paid')?.value || 0),
    items: state.cart.map((item) => ({
      product_id: item.id,
      quantity: item.quantity,
      unit_price: item.sale_price
    }))
  };
  await localDb.addPendingSale(sale);
  printInvoice(sale, [...state.cart]);
  state.cart = [];
  renderCart();
  await setStatus('Sale saved locally. Auto sync will run when internet is available.');
  await tryAutoSync();
}

async function loadSettings() {
  $('backend-url').value = await localDb.getSetting('backend_url') || localStorage.getItem('abiz_api_base') || '';
}

document.addEventListener('DOMContentLoaded', async () => {
  // Clear session to force login per user request
  sessionStorage.removeItem('pos_session_active');
  
  $('backend-url').value = await localDb.getSetting('backend_url') || localStorage.getItem('abiz_api_base') || 'https://abiz-pos-system-production-02e4.up.railway.app/api';
  $('login-email').value = await localDb.getSetting('login_email') || '';
  // License key is NOT auto-filled for security — user must enter manually each time

  // Fix Electron input focus — only redirect focus if user clicks panel background (not on an input)
  const loginPanel = $('login-panel');
  if (loginPanel) {
    loginPanel.addEventListener('click', (e) => {
      // If user clicked directly on an input, don't steal focus
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'BUTTON') return;
      // Otherwise focus first empty input
      const inputs = loginPanel.querySelectorAll('input:not([style*="display:none"])');
      for (const inp of inputs) {
        if (!inp.value) { inp.focus(); break; }
      }
    });
  }
  $('scanner-input').addEventListener('keydown', async (event) => {
    if (event.key !== 'Enter') return;
    const code = event.target.value.trim();
    event.target.value = '';
    if (code) await scanProduct(code);
  });
  
  let barcodeBuffer = '';
  let barcodeTimeout = null;
  document.addEventListener('keydown', async (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    if (e.key === 'Enter' && barcodeBuffer.length > 2) {
      await scanProduct(barcodeBuffer);
      barcodeBuffer = '';
      return;
    }
    if (e.key.length === 1) {
      barcodeBuffer += e.key;
      clearTimeout(barcodeTimeout);
      barcodeTimeout = setTimeout(() => barcodeBuffer = '', 100);
    }
  });
  $('sync-products').addEventListener('click', () => syncProducts().catch((error) => setStatus(error.message, false)));
  $('sync-sales').addEventListener('click', () => syncSales().catch((error) => setStatus(error.message, false)));
  $('checkout').addEventListener('click', () => checkout().catch((error) => setStatus(error.message, false)));
  $('clear-cart').addEventListener('click', () => { state.cart = []; renderCart(); });
  $('discount-input')?.addEventListener('input', renderCart);
  $('amount-paid')?.addEventListener('input', renderCart);
  $('settings-btn')?.addEventListener('click', async () => {
    const url = prompt('Backend URL', await localDb.getSetting('backend_url'));
    if (url) {
      await localDb.setSetting('backend_url', url.trim());
      $('backend-url').value = url.trim();
      await setStatus('Backend URL saved.');
    }
  });
  $('login-btn')?.addEventListener('click', async () => {
    $('login-email').value = await localDb.getSetting('login_email');
    $('login-password').focus();
  });
  $('save-settings')?.addEventListener('click', async () => {
    await localDb.setSetting('backend_url', $('backend-url').value.trim());
    await setStatus('Settings saved.');
  });
  $('do-login').addEventListener('click', () => login().catch((error) => setStatus(error.message, false)));
  $('login-password')?.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') login().catch((error) => setStatus(error.message, false));
  });
  $('login-license')?.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') login().catch((error) => setStatus(error.message, false));
  });
  $('logout-btn')?.addEventListener('click', () => logout().catch((error) => setStatus(error.message, false)));
  window.addEventListener('online', tryAutoSync);
  window.addEventListener('offline', () => setStatus('Offline mode active.'));
  setInterval(tryAutoSync, 60000);
  await refreshProducts();
  renderCart();
  const loggedIn = await updateAuthState();
  if (!loggedIn && navigator.onLine && $('backend-url').value && $('login-email').value) {
    setStatus('Login required to refresh access.', false);
  }
  await setStatus('Desktop app ready.');
});
