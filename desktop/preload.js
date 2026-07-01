const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('abizDesktop', {
  storage: true,
  apiRequest: (request) => ipcRenderer.invoke('api:request', request)
});
