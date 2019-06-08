'use strict';

const express = require('express');

// Constants
const PORT = 8080;
const HOST = '0.0.0.0';

// App
const app = express();
app.get('/', (req, res) => {
  res.send('Hello world\n');
});

app.listen(PORT, HOST);
console.log(`Running on http://${HOST}:${PORT}`);
/*
# $ docker build -t node-web-app .
# $ docker images
# -d runs the container in detached mode, leaving the container running in the background
# -p flag redirects a public port to a private port inside the container. 
# $ docker run -p 49160:8080 -d node-web-app
# $ docker ps // show mapping of ports.
# Test in browser navigating to http://localhost:49160/
# Test using command: curl -i localhost:49160
*/