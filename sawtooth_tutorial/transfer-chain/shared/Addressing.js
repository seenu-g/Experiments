const { createHash } = require('crypto')
const env = require('../shared/env');

const PREFIX = getAddress(env.familyName, 6)
  //const PREFIX = '19d832'

// Encoding helpers and constants
const getAddress = (key, length = 64) => {
    return createHash('sha512').update(key).digest('hex').slice(0, length)
  }

const getAssetAddress = name => PREFIX + '00' + getAddress(name, 62)
const getTransferAddress = asset => PREFIX + '01' + getAddress(asset, 62)