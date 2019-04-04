require('./people')
const cbor = require('cbor')
var protobuf = require("protobufjs");

var tname='srinivasan'
var tid = 1
var tcity ='bangalore'
function makeData(fname,fid,fcity){
    return data = {
        name: fname,
        id: fid,
        city: fcity
    }; 
}
myData = makeData(tname,tid,tcity)
// convert a JavaScript object to a string 
var json = JSON.stringify(myData); 
console.log(json); 
console.log(typeof json); // string 

// convert a JSON string to a JavaScript object 
var data = JSON.parse(json); 
console.log(data.name); 
console.log(data.id); 
console.log(data.city); 

strBuffer = Buffer.from(data.name +":" + data.id + ":"+ data.city);
console.log(strBuffer)
console.log(strBuffer.toString().split(':'))

const newPayload = {
    Verb: 'set',
    Name: 'name',
    Value: 1
  }
  const payloadBytes = cbor.encode(newPayload)
  console.log(payloadBytes)

  temp  = cbor.decode(payloadBytes)
  console.log(temp)

  demo = protobuf.roots.default.demo
  const People = demo.People;
  const Person = demo.Person;
  const Address = demo.Address;

    var protobuf = require("protobufjs");
    var protos = require("./model.js")

    var mock1 = protos.model.Collection.create()
    mock1.name = "mock collection"
    mock1.createdTsMicros = 123456
    mock1.description = "simple mock collection"
    mock1.subscriberIds = []
    console.log(mock1)

    var mock2 = protos.model.Collection.create()
    mock2.name = "mock collection 2"
    mock2.createdTsMicros = 123456
    mock2.description = "simple mock collection 2"
    mock2.subscriberIds = []
    console.log(mock2)
    
    var item1 = protos.model.Item.create()
    item1.id = "item1"
    item1.url ="http://google.com"
    item1.created_ts_micros = 1
    item1.author_id = "author1"
    console.log(item1)

    var user1 = protos.model.User.create()
    user1.id = 1225
    console.log(user1)

    var data = {name:"mock collection3",description: "descriptuion 3",createdTsMicros:56789}
    console.log(protos.model.Collection.verify(data))
    var mock3 = protos.model.Collection.fromObject(data)
    console.log(mock3)

    var protos = require("./record.js")
    var record1 = protos.model.Record.create()
    record1.record_id = 5
    var location = protos.model.Record.Location.create()
    location.latitude = 16
    location.longitude = 85
    location.timestamp = 23456
    record1.locations.push(location)
    record1.locations.push(location)
    var owner = protos.model.Record.Owner.create()
    owner.agent_id = 5
    owner.timestamp =25678
    record1.owners.push(owner)
    record1.owners.push(owner)

    console.log(record1)

    var container = protos.model.RecordContainer.create()
    container.entries.push(record1)
    container.entries.push(record1)
    console.log(container)




    


  