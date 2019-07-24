const mongoose = require('mongoose')

const Schema = mongoose.Schema

const userSchema = new Schema({
  name:String,
  password1:String,
  address:String,
  balance:String,
  faddres:String,
  taddress:String,
  ether:String
})

module.exports=mongoose.model('account',userSchema,'accounts')