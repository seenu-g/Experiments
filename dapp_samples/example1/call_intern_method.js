console.log('Setting up...');
const solc = require ('solc');
const Web3 = require ('web3');
console.log('Reading abi');
const HelloWorldABI = require("./HelloWorldABI.json");
console.log('Connecting');
const web3 = new Web3(new Web3.providers.HttpProvider("http://localhost:8545"));
const tempContract = web3.eth.contract(HelloWorldABI);
var tempContractInstance = tempContract.at("0x0a2458001884cd316e23930f3b9cb115faf09430");
console.log(tempContractInstance.setProfileData);
console.log('unlocking local geth account');

// this is to set employer's acccount and  set profile data
const password1 = "810";
try {
    web3.personal.unlockAccount("0x2463f4C2404Ac36ebe5DA89bFe788ddFA8D11C47", password1);
} catch (e) {
    console.log(e);
    return;
}

tempContractInstance.setProfileData("santhosh","8105823673","santh@gmil.com",1995,"104",{
    from:"0x2463f4C2404Ac36ebe5DA89bFe788ddFA8D11C47",
    gas:4000000},function (error, result){ 
        if(!error){
            console.log(result);
        } else{
            console.log(error);
        }
});

// this is to call getProfiledata by specific pan number
console.log(tempContractInstance.getProfileData.call("104"));

// this is to set intern and confirm it for interview
const password2 = "321";
try {
    web3.personal.unlockAccount("0x57e67649f439a855c6e448d77304820e4bc6225f", password2);
} catch (e) {
    console.log(e);
    return;
}


tempContractInstance.confirmProfile("104",{
    from: "0x57e67649f439a855c6e448d77304820e4bc6225f",
    gas:4000000},function (error, result){ 
        if(!error){
            console.log(result);
        } else{
            console.log(error);
        }
});


// here employer calls intern for interview 
const password3 = "810";
try {
    web3.personal.unlockAccount("0x2463f4C2404Ac36ebe5DA89bFe788ddFA8D11C47", password3);
} catch (e) {
    console.log(e);
    return;
}

tempContractInstance.CallforInterview("104",{
    from:"0x2463f4C2404Ac36ebe5DA89bFe788ddFA8D11C47",
    gas:4000000},function (error, result){ 
        if(!error){
            console.log(result);
        } else{
            console.log(error);
        }
});


// here employer sets the results of interview to an intern
const password4 = "810";
try {
    web3.personal.unlockAccount("0x2463f4C2404Ac36ebe5DA89bFe788ddFA8D11C47", password4);
} catch (e) {
    console.log(e);
    return;
}

tempContractInstance.setInterviewResult("104","pass","6months",15000,{
    from:"0x2463f4C2404Ac36ebe5DA89bFe788ddFA8D11C47",
    gas:4000000},function (error, result){ 
        if(!error){
            console.log(result);
        } else{
            console.log(error);
        }
});


//here intern can view the result 
console.log(tempContractInstance.getInterviewResult.call("104"));