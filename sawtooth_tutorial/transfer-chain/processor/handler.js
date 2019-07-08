'use strict'
onst { TransactionHandler } = require('sawtooth-sdk/processor/handler')
const { InvalidTransaction, InternalError } = require('sawtooth-sdk/processor/exceptions')
const cbor = require('cbor')
const env = require('../shared/env');
const { createHash } = require('crypto')

const { TransactionHeader } = require('sawtooth-sdk/protobuf')
const { getAssetAddress } = require('../shared/Addressing')
const { getTransferAddress } = require('../shared/Addressing')

const encode = obj => Buffer.from(JSON.stringify(obj, Object.keys(obj).sort()))
const decode = buf => JSON.parse(buf.toString())

// Add a new asset to state
const createAsset = (asset, owner, state) => {
  const asset_address = getAssetAddress(asset)

  return state.get([asset_address]).then(entries => {
      const entry = entries[asset_address]
      if (entry && entry.length > 0) {
        throw new InvalidTransaction('Asset name in use')
      }

      return state.set({
        [asset_address]: encode({name: asset, owner})
      })
    })
}

// Add a new transfer to state
const transferAsset = (asset, owner, signer, state) => {
  const transfer_address = getTransferAddress(asset)
  const asset_address = getAssetAddress(asset)

  return state.get([asset_address]).then(entries => {
      const entry = entries[asset_address]
      if (!entry || entry.length === 0) {
        throw new InvalidTransaction('Asset does not exist')
      }
      if (signer !== decode(entry).owner) {
        throw new InvalidTransaction('Only an Asset\'s owner may transfer it')
      }
      return state.set({
        [transfer_address]: encode({asset, owner})
      })
    })
}

// Accept a transfer, clearing it and changing asset ownership
const acceptTransfer = (asset, signer, state) => {
  const transfer_address = getTransferAddress(asset)

  return state.get([transfer_address]).then(entries => {
      const entry = entries[transfer_address]
      if (!entry || entry.length === 0) {
        throw new InvalidTransaction('Asset is not being transfered')
      }

      if (signer !== decode(entry).owner) {
        throw new InvalidTransaction( 'Transfers can only be accepted by the new owner')
      }

      return state.set({
        [transfer_address]: Buffer(0),
        [getAssetAddress(asset)]: encode({name: asset, owner: signer})
      })
    })
}

// Reject a transfer, clearing it
const rejectTransfer = (asset, signer, state) => {
  const transfer_address = getTransferAddress(asset)

  return state.get([transfer_address]).then(entries => {
      const entry = entries[transfer_address]
      if (!entry || entry.length === 0) {
        throw new InvalidTransaction('Asset is not being transfered')
      }

      if (signer !== decode(entry).owner) {
        throw new InvalidTransaction('Transfers can only be rejected by the potential new owner')
      }

      return state.set({
        [transfer_address]: Buffer(0)
      })
    })
}

class TransferHandler extends TransactionHandler {
  constructor () {
    console.log('Initializing JSON handler for Transfer-Chain')
    super(FAMILY, '0.0', 'application/json', [PREFIX])
  }

  apply (txn, state) {
    // Parse the transaction header and payload
    const header = TransactionHeader.decode(txn.header)
    const signer = header.signerPubkey
    const { action, asset, owner } = JSON.parse(txn.payload)

    if (action === 'create') return createAsset(asset, signer, state)
    if (action === 'transfer') return transferAsset(asset, owner, signer, state)
    if (action === 'accept') return acceptTransfer(asset, signer, state)
    if (action === 'reject') return rejectTransfer(asset, signer, state)

    return Promise.resolve().then(() => {
           throw new InvalidTransaction('Action must be "create", "transfer", "accept", or "reject"')
    })
  }
}

module.exports = TransferHandler;