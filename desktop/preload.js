const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('abizDesktop', {
  storage: true
});
