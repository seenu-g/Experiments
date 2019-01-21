pragma solidity ^0.4.25;
contract MagicStone{
    address public creator;
    mapping (address => uint) balances;
    
    event Transferred(address from, address to, uint amount);
    
    constructor() public{
        creator = msg.sender;
        balances[msg.sender]=100;
    }
    
    function create(address receiver,uint amount) public{
        require(msg.sender ==creator);
        balances[receiver] += amount;
    }
    
    function transfer(address receiver,uint amount) public{
        require(balances[msg.sender]> amount);
        balances[msg.sender] -= amount;
        balances[receiver] += amount;
        emit Transferred(msg.sender,receiver,amount);
    }
}