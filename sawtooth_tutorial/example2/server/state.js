var { _hash } = require("./lib");
var { TP_NAMESPACE } = require("./constants");

class SimpelStoreState {
 constructor(context) {
   this.context = context;
   this.timeout = 500;
   this.stateEntries = {};
 }

 setValue(tag,value) {
   //var address = makeAddress(value);
   var address = makeAddress(tag);
   var stateEntriesSend = {}
   //stateEntriesSend[address] = Buffer.from("Hello! " + value);
   stateEntriesSend[address] = Buffer.from(tag + value);
   return  this.context.setState(stateEntriesSend, this.timeout).then(function(result) {
     console.log("Success", result)
   }).catch(function(error) {
     console.error("Error", error)
   })
 }

 getValue(tag,value) {
   //var address = makeAddress(value);
   var address = makeAddress(tag);
   return  this.context.getState([address], this.timeout).then(function(stateEntries) {
     Object.assign(this.stateEntries, stateEntries);
     console.log(this.stateEntries[address].toString())
     return  this.stateEntries;
   }.bind(this))
 }
}

const makeAddress = (x, label) => TP_NAMESPACE + _hash(x)

module.exports = SimpelStoreState;