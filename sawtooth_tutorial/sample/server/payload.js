const { InvalidTransaction, InternalError } = require('sawtooth-sdk/processor/exceptions')
class XoPayload {
    constructor (name, action, space) {
        this.name = name
        this.action = action
        this.space = space
    }

    static fromBytes (payload) {
        payload = payload.toString().split(',')
        if (payload.length === 3) {
            let xoPayload = new XoPayload(payload[0], payload[1], payload[2])
            if (!xoPayload.name) {
                throw new InvalidTransaction('Name is required')
            }
            if (xoPayload.name.indexOf('|') !== -1) {
                throw new InvalidTransaction('Name cannot contain "|"')
            }

            if (!xoPayload.action) {
                throw new InvalidTransaction('Action is required')
            }
            return xoPayload
        } else {
        throw new InvalidTransaction('Invalid payload serialization')
        }
    }
}
module.exports = XoPayload