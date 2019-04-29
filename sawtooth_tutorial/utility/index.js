const  CryptManager = require('./cryptmanager');
const crypto = require("crypto");
var secretManager = new CryptManager();

const secret = 'santo';

let key = crypto.createHash('sha256').update(String(secret)).digest('base64').substr(0, 32);
var IV = new Buffer(crypto.randomBytes(16)); 
encryptedString = secretManager.encrypt("abc",key,IV)
console.log(encryptedString)

decryptedString = secretManager.decrypt(encryptedString,key,IV)
console.log(decryptedString)
