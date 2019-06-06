var zmq = require('zeromq')
  , sock = zmq.socket('pub');
var counter = 0;
sock.bindSync('tcp://127.0.0.1:3000');
console.log('Publisher bound to port 3000');

function sendMessage (message) {
  console.log("[" + new Date().toLocaleTimeString() + "] " + message);
  sock.send(message);
}
/*setInterval(function(){
  console.log('sending a multipart message envelope');
  sock.send(['kitty cats', 'meow!']);
}, 500); */

setInterval(function () { 
  var temp = counter++;
  console.log ('sending counter',temp )
  sock.send(['kitty cats', temp.toString()]);
}, 1000);


