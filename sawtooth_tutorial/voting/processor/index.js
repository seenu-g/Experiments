
const { TransactionProcessor } = require('sawtooth-sdk/processor')

const VotingHandler = require('./handler')
const env = require('../shared/env')

const transactionProcessor = new TransactionProcessor(env.validatorUrl)

transactionProcessor.addHandler(new VotingHandler())
transactionProcessor.start()

console.log(`Starting VotingHandler processor`)
console.log(`Connecting to Sawtooth validator at ${env.validatorUrl}`)
