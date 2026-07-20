const { app, BrowserWindow } = require('electron');
const path = require('path');


app.commandLine.appendSwitch('disable-gpu-shader-disk-cache');
app.commandLine.appendSwitch('disk-cache-size', '1');

// Allow multiple instances
const gotTheLock = true;

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 760,
    minWidth: 980,
    minHeight: 640,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: false
    }
  });

  win.loadFile(path.join(__dirname, 'renderer', 'mode_select.html'));
}

app.disableHardwareAcceleration();

if (gotTheLock) {
  app.whenReady().then(createWindow);

  app.on('second-instance', (event, commandLine, workingDirectory) => {
    const wins = BrowserWindow.getAllWindows();
    if (wins.length) {
      if (wins[0].isMinimized()) wins[0].restore();
      wins[0].focus();
    }
  });

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
  });
}