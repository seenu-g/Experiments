var abi = require('ethereumjs-abi')
var BN = require('bn.js')

console.log(abi.soliditySHA3(
    [ "address", "string", "string", "string" ],
    [ "0xca35b7d915458ef540ade6068dfe2f44e8fa733c", "1", "battery","today" ]
).toString('hex'))