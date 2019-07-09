'use strict'
const { TransactionHandler } = require('sawtooth-sdk/processor/handler')
const { InvalidTransaction, InternalError } = require('sawtooth-sdk/processor/exceptions')
const cbor = require('cbor')
const env = require('../shared/env');

const crypto = require('crypto')

const {TextEncoder, TextDecoder} = require('text-encoding/lib/encoding')
const _hash = (x) => crypto.createHash('sha512').update(x).digest('hex').toLowerCase()
var encoder = new TextEncoder('utf8')
var decoder = new TextDecoder('utf8')

const { _decodeRequest } = require('./decodeRequest')
const { voterUpload,candidateUpload,vote,setVote} = require('./state')

class VotingHandler extends TransactionHandler{
    constructor(){
        super(env.familyName, [env.familyVersion], [env.TP_NAMESPACE])
    }
    apply(transactionProcessRequest, context){
      return _decodeRequest(transactionProcessRequest.payload).catch(_toInternalError)
        .then((parameters) => {
                                                                                                                                                        let header = transactionProcessRequest.header
        let action = parameters.action
        console.log("returned with action value:",action)
        if (!action) {
            throw new InvalidTransaction('Action is required')
        }
         //validation of voter-upload
         if(action === 'voter-upload'){
            let name = parameters.name
            if (name === null || name === undefined) {
                throw new InvalidTransaction('Value is required')
            }
            if (typeof name !== "string" ||  name.length < 1) {
                throw new InvalidTransaction(`Value must contain only characters ` + `no less than 1`)
            }
            let id = parameters.id;
            let idNum = parseInt(id);
            console.log("ID :",idNum,'length:',id.length)
            if( id.length != 16){
                throw new InvalidTransaction(`Id must be a numerical value ` + `must contain 16 digits`)
            }
            let actionFn
            let Address
            Address = env.TP_NAMESPACE +_hash(parameters.id).substring(0,64) 
            //console.log('address:',Address)
            actionFn = voterUpload
        }       
        else if(action === 'candidate-upload'){
            let name = parameters.name
            console.log("the name of candidate:",name)
            if (name === null || name === undefined) {
                throw new InvalidTransaction('Value is required')
            }
            if (typeof name !== "string" ||  name.length < 1) {
                throw new InvalidTransaction(`Value must contain only characters ` + `no less than 1`)
            }
            let sign = parameters.caSign
            console.log("Sign :",sign)
            Address = env.TP_NAMESPACE +_hash(parameters.station).substring(0,64)
            //console.log('address:',Address)
            actionFn = candidateUpload
        }
        //validation of vote
        else if(action === 'vote'){
            let CandidateIndex = parameters.CandidateIndex
            console.log("the Index of the candidate:",CandidateIndex)
            CandidateIndex = parseInt(CandidateIndex)
    
            if (CandidateIndex === null || CandidateIndex === undefined) {
                throw new InvalidTransaction('Value is required')
            }
            if (typeof CandidateIndex !== "number" ||  CandidateIndex.length < 1) {
                throw new InvalidTransaction(`Value must contain only numbers` + `no less than 1`)
            }
            let station = parameters.station;
            if(station === null || station === undefined){
            throw new InvalidTransaction('Station is required')
            }
        
            Address = env.TP_NAMESPACE +_hash(station).substring(0,64)
            //console.log('address:',Address)
            actionFn = vote
          }
        else if(action === 'setVote'){
            let voterId = parameters.voterId;
            let idNum = parseInt(voterId);
            console.log("ID :",idNum,'length:',voterId.length)
  
            if( voterId.length != 16 ){
                throw new InvalidTransaction( `must contain 16 digits`)
            }
            Address = env.TP_NAMESPACE +_hash(voterId).substring(0,64)
            //console.log('address:',Address)
            actionFn = setVote
        }
        else{
              throw new InvalidTransaction('Unknown action!!')
        }
        // Get the current state, for the key's address
        let getPromise
        if (parameters.action == 'voter-upload')
            getPromise = context.getState([Address])
        else
            getPromise = context.getState([Address])
        let actionPromise = getPromise.then(actionFn(context,Address, parameters))
        return actionPromise.then(addresses => {
            if (addresses.length === 0) {
                throw new InternalError('State Error!')
            }  
        })
    })
   }
  }

  const _toInternalError = (err) => {
    console.log(" in error message block")
    let message = err.message ? err.message : err
    throw new InternalError(message)
  }
  module.exports = VotingHandler