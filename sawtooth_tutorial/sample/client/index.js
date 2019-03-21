const {createContext, CryptoFactory} = require('sawtooth-sdk/signing')
const {createHash} = require('crypto')
const {protobuf} = require('sawtooth-sdk')

const context = createContext('secp256k1')
const privateKey = context.newRandomPrivateKey()
const signer = new CryptoFactory(context).newSigner(privateKey)

const cbor = require('cbor')
const payload = {
    Verb: 'set',
    Name: 'foo',
    Value: 42
//    name: 'game1',
//    action: 'create',
//    space: 1
}
const payloadBytes = cbor.encode(payload)
//node index.js  '{"name": "game1", "action": "create"}'
//node index.js  '{"name": "game1","action": "take","space" :"Name"}'
//name values: game1, game2, game 3
//action values: create, delete, take
//space value: 1-9 (inclusive), if the action is take

const transactionHeaderBytes = protobuf.TransactionHeader.encode({
    familyName: 'xo1',
    familyVersion: '1.0',
    inputs: ['1cf1266e282c41be5e4254d8820772c5518a2c5a8c0c7f7eda19594a7eb539453e1ed7'],
    outputs: ['1cf1266e282c41be5e4254d8820772c5518a2c5a8c0c7f7eda19594a7eb539453e1ed7'],
    signerPublicKey: signer.getPublicKey().asHex(),
    // In this example, we're signing the batch with the same private key,
    // but the batch can be signed by another party, in which case, the
    // public key will need to be associated with that key.
    batcherPublicKey: signer.getPublicKey().asHex(),
    // In this example, there are no dependencies.  This list should include
    // an previous transaction header signatures that must be applied for
    // this transaction to successfully commit.
    // For example,
    // dependencies: ['540a6803971d1880ec73a96cb97815a95d374cbad5d865925e5aa0432fcf1931539afe10310c122c5eaae15df61236079abbf4f258889359c4d175516934484a'],
    dependencies: [],
    payloadSha512: createHash('sha512').update(payloadBytes).digest('hex')
}).finish()

const transactionSignature = signer.sign(transactionHeaderBytes)
const transaction = protobuf.Transaction.create({
    header: transactionHeaderBytes,
    headerSignature: transactionSignature,
    payload: payloadBytes
})

const transactions = [transaction]
const batchHeaderBytes = protobuf.BatchHeader.encode({
    signerPublicKey: signer.getPublicKey().asHex(),
    transactionIds: transactions.map((txn) => txn.headerSignature),
}).finish()

const batchSignature = signer.sign(batchHeaderBytes)
const batch = protobuf.Batch.create({
    header: batchHeaderBytes,
    headerSignature: batchSignature,
    transactions: transactions
})

const batchListBytes = protobuf.BatchList.encode({
    batches: [batch]
}).finish()

const request = require('request')

request.post({
    url: 'http://localhost:8008/batches',
    body: batchListBytes,
    headers: {'Content-Type': 'application/octet-stream'}
}, (err, response) => {
    if (err) return console.log(err)
    console.log(response.body)
})