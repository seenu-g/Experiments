var express = require('express');
var app = express();
var fs = require("fs");

app.use(express.static('public'));
app.get('/form_data_get.html', function (req, res) {
   res.sendFile( __dirname + "/" + "form_data_get.html" );
})
app.get('/form_data_post.html', function (req, res) {
    res.sendFile( __dirname + "/" + "form_data_post.html" );
 })
 app.get('/file_upload.html', function (req, res) {
    res.sendFile( __dirname + "/" + "file_upload.html" );
 })

app.get('/process_get', function (req, res) {
   // Prepare output in JSON format
   response = {
      first_name:req.query.first_name,
      last_name:req.query.last_name
   };
   console.log("process_get", response);
   res.end(JSON.stringify(response));
})

var bodyParser = require('body-parser');
// Create application/x-www-form-urlencoded parser
var urlencodedParser = bodyParser.urlencoded({ extended: false })
app.post('/process_post', urlencodedParser, function (req, res) {
   // Prepare output in JSON format
   response = {
      first_name:req.body.first_name,
      last_name:req.body.last_name
   };
   console.log("process_post", response);
   res.end(JSON.stringify(response));
})

var multer  = require('multer');

app.post('/file_upload', function (req, res) {
    app.use(multer({dest:'./uploads/'}).single('singleInputFileName'));
    console.log(req)
    /* console.log(req.files.file.name);
    console.log(req.files.file.path);
    console.log(req.files.file.type);
    var file = __dirname + "/" + req.files.file.name;
    
    fs.readFile( req.files.file.path, function (err, data) {
       fs.writeFile(file, data, function (err) {
          if( err ) {
             console.log( err );
             } else {
                response = {
                   message:'File uploaded successfully',
                   filename:req.files.file.name
                };
             }
          
          console.log( response );
          res.end( JSON.stringify( response ) );
       });
    }); */
 })
 
var server = app.listen(8081, function () {
   var host = server.address().address
   var port = server.address().port
   
   console.log("Example app listening at http://%s:%s", host, port)
})

//https://www.tutorialspoint.com/nodejs/nodejs_express_framework.htm