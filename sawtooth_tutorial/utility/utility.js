const randomString = require("randomstring");
utility.prototype.getDocumentHash = function (documentData) {
    return crypto.createHash('sha256').update(documentData).digest('hex');
}
utility.prototype.randomAplhaNumber = function (size) {
    var chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        result = ""
    for (var i = 0; i < size; ++i)
        result += chars[Math.round(Math.random() * (chars.length - 1))];
    return result;
}

utility.prototype.randomNDigitNumber = function (size) {
    var r = (Math.random() * Math.pow(10, size)).toFixed(0);
    while (r.length != size)
        r = "0" + r;
    return r;
}
utility.prototype.generateRandomBytes = function (size) {
    return crypto.randomBytes(size);
}

utility.prototype.generateRandomString = function (size) {
    return randomString.generate(size);
}


utility.prototype.hex2bin = function (hex) {
    return Buffer.from(hex, 'hex');
}

utility.prototype.bin2hex = function (bin) {
    return Buffer.from(bin).toString('hex');
}

utility.prototype.hex2str = function (hex) {
    return Buffer.from(hex, 'hex').toString('utf-8');
}

utility.prototype.str2hex = function (str) {
    return Buffer.from(str).toString('hex');
}

utility.prototype.json2hex = function (json) {
    return this.str2hex(JSON.stringify(json));
}

utility.prototype.json2str = function (json) {
    return JSON.stringify(json);
}

utility.prototype.str2json = function (json) {
    return JSON.parse(json);
}

utility.prototype.hex2json = function (hex) {
    let data = this.hex2str(hex);
    try {
        return JSON.parse(data);
    }
    catch (ex) {
        return data;
    }
}
 module.exports =  utility ;
