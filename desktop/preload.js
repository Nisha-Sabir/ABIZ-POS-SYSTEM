const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('abiz', {
  getSetting: (key) => ipcRenderer.invoke('settings:get', key),
  setSetting: (key, value) => ipcRenderer.invoke('settings:set', key, value),
  upsertProducts: (products) => ipcRenderer.invoke('products:upsertMany', products),
  findProductByCode: (code) => ipcRenderer.invoke('products:findByCode', code),
  listProducts: () => ipcRenderer.invoke('products:list'),
  saveOfflineSale: (sale) => ipcRenderer.invoke('sales:saveOffline', sale),
  getPendingSales: () => ipcRenderer.invoke('sales:pending'),
  markSalesSynced: (ids) => ipcRenderer.invoke('sales:markSynced', ids)
});
