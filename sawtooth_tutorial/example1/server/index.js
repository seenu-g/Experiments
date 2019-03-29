const { TransactionProcessor } = require('sawtooth-sdk/processor')

const IntegerKeyHandler = require('./intkey_handler')
const env = require('./env')

const transactionProcessor = new TransactionProcessor(env.validatorUrl)

transactionProcessor.addHandler(new IntegerKeyHandler())
transactionProcessor.start()

console.log(`Starting example1 transaction processor`)
console.log(`Connecting to Sawtooth validator at ${env.validatorUrl}`)