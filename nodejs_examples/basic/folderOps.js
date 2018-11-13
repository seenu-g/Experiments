// create folder called testFolder and run command "chmod 777 testfolder" to run this code.

var fs = require("fs");
var err = null

function readFileFolder( value) {
    console.log("Going to read directory " + value);
    fs.readdir(value, function(err, files) {
        if (err) {
            return console.error(err);
            }
        files.forEach(function(file) {
            console.log(file);
        });
    });
}
function createFolder(value) {
    console.log("Going to create directory " + value);
    fs.mkdir(value, function(err) {
        if(err != null && err != '') {
            if(err.code != 'EEXIST')
                return console.error(err);
            else {
                console.log("Directory already present");
                readFileFolder(value)
            }
        }
        else {
            console.log("Directory created successfully!");
            readFileFolder(value)
        }
    });
}

/*
for (let j = 0; j < process.argv.length; j++) {  
    console.log(j + ' -> ' + (process.argv[j]));
} */
// create folder called testFolder and run command "chmod 777 testfolder" to run this code.

createFolder("testFolder/" + process.argv[2])
