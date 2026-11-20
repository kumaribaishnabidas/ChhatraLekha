'use strict'

const path = require('node:path')
const { app, BrowserWindow, Menu, shell } = require('electron')
const { parsePortalUrl, isInternalPortalUrl } = require('./url-policy.cjs')

const APP_URL = process.env.CHHATRALEKHA_WEB_URL || 'https://chhatralekha.vercel.app/'
const OFFLINE_PAGE = `file://${path.join(__dirname, 'offline.html')}`
let mainWindow

function createWindow() {
  const portalUrl = parsePortalUrl(APP_URL)
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 900,
    minHeight: 620,
    show: false,
    autoHideMenuBar: true,
    backgroundColor: '#f8f9fa',
    webPreferences: {
      partition: 'chhatralekha-linux',
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      webviewTag: false,
      plugins: false,
    },
  })

  mainWindow.webContents.session.setPermissionRequestHandler(
    (_webContents, _permission, callback) => callback(false),
  )

  mainWindow.once('ready-to-show', () => mainWindow.show())

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/.test(url)) shell.openExternal(url).catch(() => {})
    return { action: 'deny' }
  })

  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (url === OFFLINE_PAGE) return
    if (!isInternalPortalUrl(url, portalUrl.href)) {
      event.preventDefault()
      if (/^https?:/.test(url)) shell.openExternal(url).catch(() => {})
    }
  })

  mainWindow.webContents.on('will-redirect', (event, url) => {
    if (url !== OFFLINE_PAGE && !isInternalPortalUrl(url, portalUrl.href)) event.preventDefault()
  })

  mainWindow.webContents.on('did-fail-load', (_event, errorCode, _description, _url, isMainFrame) => {
    if (isMainFrame && errorCode !== -3 && mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.loadFile(path.join(__dirname, 'offline.html')).catch(() => {})
    }
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  mainWindow.loadURL(portalUrl.href).catch(() => {})
}

if (!app.requestSingleInstanceLock()) {
  app.quit()
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore()
      mainWindow.focus()
    }
  })

  app.whenReady().then(() => {
    Menu.setApplicationMenu(null)
    createWindow()
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow()
    })
  })

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit()
  })
}
