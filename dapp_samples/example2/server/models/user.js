const mongoose = require('mongoose')

const Schema = mongoose.Schema

const userSchema = new Schema({
    dob:String, 
    email:String,
    firstname:String,
    gender:String,
    lastname:String,
    password:String,
    phonenumber:Number,
    state:String,  
    isadmin:String 
})

module.exports=mongoose.model('user',userSchema,'users')