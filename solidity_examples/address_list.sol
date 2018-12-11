pragma solidity ^0.4.23;
contract AddressList {  
    event addressregistered(address addy);

    address[] public MemberAddresses;
    address public deployer;
    
    struct Member {
        string name;
    }
    mapping(address => Member) public members;
    
    constructor() public {
        deployer = msg.sender;
    }
    function registerAddress(string _name) public { 
        MemberAddresses.push(msg.sender);    
        members[msg.sender].name = _name;
        emit addressregistered(msg.sender);
        }  
    function getAllBought() public constant returns(address[]) {
        return MemberAddresses;
    }
}
