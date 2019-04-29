const crypto = require("crypto");
function CryptManager() {
    
}
CryptManager.prototype.encrypt = function (text, key,initVector) {
    var cipher = crypto.createCipheriv("aes-256-ctr", key,initVector)
    var crypted = cipher.update(text, 'utf8', 'hex')
    crypted += cipher.final('hex');
    return crypted;
}

CryptManager.prototype.decrypt = function (text, key,initVector) {
    var decipher = crypto.createDecipheriv("aes-256-ctr", key,initVector)
    var decrypted = decipher.update(text, 'hex', 'utf8')
    decrypted += decipher.final('utf8');
    return decrypted;
}

/*
 // Generating password by calling a function from common utility file to encrypt the file data
    let password = common_utility.generateRandomString(32);
 // Generating the iv(initialization vector) by calling a function from common utility, is used to passed along with the password. 
    let iv = common_utility.generateRandomString(12);

_get_state_data(uniqueKey, addr, updatedAddress) {
			var updatedAddress = this.address + hash(addr).substr(0, 64);
			var geturl = 'http://localhost:8008/state/'+updatedAddress
		    return fetch(geturl, {
 		    	method: 'GET',
		    })
		   	.then((response) => response.json())
		   	.then((responseJson) => {
				var data = responseJson.data; 
				var stringData = new Buffer(data, 'base64').toString();
                return stringData;
		   	})
		   	.catch((error) => {
 		   		console.error(error);
		  	}); 	
	};	*/
module.exports =  CryptManager ;