const cbor = require('cbor')
var protobuf = require("protobufjs");
var protos = require("./payload.js")

var createAgentMessage = protos.model.CreateAgentAction.create()
createAgentMessage.name ="srinivasan"

var createRecordMessage = protos.model. CreateRecordAction.create()
createRecordMessage.record_id = 1
createRecordMessage.latitude = 23
createRecordMessage.longitude = 43

var updateRecordMessage = protos.model.UpdateRecordAction.create()
updateRecordMessage.record_id = 1
updateRecordMessage.latitude = 23
updateRecordMessage.longitude = 43

var transferRecordMessage = protos.model.TransferRecordAction.create()
transferRecordMessage.record_id = 1
transferRecordMessage.receiving_agent = 63

var payload1 = protos.model.PayLoad.create()
payload1.action = protos.model.PayLoad.Action.CREATE_AGENT;
payload1.create_agent = createAgentMessage;
console.log(payload1)

var payload2 = protos.model.PayLoad.create()
payload2.action = protos.model.PayLoad.Action.CREATE_RECORD;
payload2.create_record = createRecordMessage;
console.log(payload2)

var payload3 = protos.model.PayLoad.create()
payload3.action = protos.model.PayLoad.Action.UPDATE_RECORD;
payload3.update_record = updateRecordMessage;
console.log(payload3)

var payload4 = protos.model.PayLoad.create()
payload4.action = protos.model.PayLoad.Action.TRANSFER_RECORD;
payload4.transfer_record = transferRecordMessage;
console.log(payload4)