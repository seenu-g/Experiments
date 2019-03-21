const { TransactionProcessor } = require('sawtooth-sdk/processor')
const XOHandler = require('./handler')

// In docker, the address would be the validator's container name
// with port 4004
const address = 'tcp://127.0.0.1:4004'
const transactionProcessor = new TransactionProcessor(address)

transactionProcessor.addHandler(new XOHandler())

transactionProcessor.start()