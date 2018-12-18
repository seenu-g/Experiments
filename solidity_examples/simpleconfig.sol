pragma solidity ^0.4.23;
    
contract SimpleConfig {
   
   struct Account {
        string name;
        uint balance;
        uint dailyLimit;
    }
    
    uint private httpPort = 80;
    string private dbname;
    string private dbString = "database";
    Account private myAccount;

    function getValue(string  _name) public  returns (string) {
       if (stringCompare(_name,dbString))
           return dbname;
    }
    
    function stringCompare(string a, string b) public returns (bool){
       return keccak256(a) == keccak256(b);
   }

    function setValue(string _value, string _name) public{
       if (stringCompare(_name,dbString))
           dbname = _value;
    }
    
    function getPort() public view returns (uint) {
        return httpPort;
    }
    
    function setAccount(string _name,uint _balance, uint _limit) public{
        myAccount.name = _name;
        myAccount.balance = _balance;
        myAccount.dailyLimit = _limit;
    }
    
    function getAccount() view public returns(string,uint,uint) {
        return(myAccount.name,myAccount.balance,myAccount.dailyLimit);
    }
}