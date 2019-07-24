const express= require('express')
const bodyParser=require('body-parser')

var cors = require('cors');
const PORT=3000
const api=require('./api');
const app=express()

app.use(express.static('static'));
app.use(bodyParser.json())
app.use(cors());
app.use('/api',api)

app.get('/',function(req,res){
    res.send("hello from server")
})

app.listen(PORT,function(){
    console.log('the server running on port:'+PORT)
})
