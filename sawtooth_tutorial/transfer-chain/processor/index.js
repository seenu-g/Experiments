
const { TransactionProcessor } = require('sawtooth-sdk/processor')

const TransferHandler = require('./handler')
const env = require('../shared/env')

const transactionProcessor = new TransactionProcessor(env.validatorUrl)

transactionProcessor.addHandler(new TransferHandler())
transactionProcessor.start()

console.log(`Starting TransferHandler processor`)
console.log(`Connecting to Sawtooth validator at ${env.validatorUrl}`)
