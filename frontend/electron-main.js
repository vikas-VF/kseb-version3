const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let backendProcess = null;

function startBackend() {
    const backendExe = path.join(process.resourcesPath, 'backend', 'kseb-backend.exe');
    console.log('Starting backend:', backendExe);
    backendProcess = spawn(backendExe, [], { windowsHide: true });
}

app.on('ready', async () => {
    startBackend();
    await new Promise(resolve => setTimeout(resolve, 5000));

    const win = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true
        }
    });

    win.loadFile(path.join(__dirname, 'dist', 'index.html'));
});

app.on('quit', () => {
    if (backendProcess) backendProcess.kill();
});
