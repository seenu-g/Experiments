Change 1:
Rename payload.txt to payload.js

Change 2: prepareTransaction.js
Modify the code that encodes payload to encode protobuf based payload
payload1 = protobuf1(payload);
console.log("protobuf returned", payload1)
const payloadBytes = cbor.encode(payload1) 

Change 3: prepareTransaction.js
Ensure statements are present
const { protobuf } = require('sawtooth-sdk')
const { protobuf1 } = require('./payload');