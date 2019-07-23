const {app, BrowserWindow} = require('electron')
const url = require('url')
const path = require('path')

let window = null

function createWindow() {
   window = new BrowserWindow({width: 800, height: 600})
   window.loadURL(url.format ({
      pathname: path.join(__dirname, 'index.html'),
      protocol: 'file:',
      slashes: true
   }))
}

app.on('ready', createWindow)