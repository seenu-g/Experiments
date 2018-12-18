pragma solidity ^0.4.23;

contract SharedWallet {
    
    address public regulator;
    mapping(address => uint8) private holders; 

    modifier isRegulator() {
        require(msg.sender == regulator);
        _;
    }
    
    modifier validHolder {
        require(msg.sender == regulator || holders[msg.sender] == 1);
        _;
    }
    
    event DepositFunds(address from, uint amount);
    event WithdrawFunds(address to, uint amount);
    event TransferFunds(address from, address to, uint amount);
    
    constructor()  public {
        regulator = msg.sender;
    }
    
    function addMember(address member) public{
        require(msg.sender == regulator);
        holders[member] = 1;
    }
    
    function removeMember(address member) public{
        require(msg.sender == regulator);
        holders[member] = 0;
    }
    
    function deposit() public payable {
        emit DepositFunds(msg.sender, msg.value);
    }
    
    function withdraw(uint amount) validHolder  public {
        require(address(this).balance >= amount);
        msg.sender.transfer(amount);
        emit WithdrawFunds(msg.sender, amount);
    }
    
    function transferTo(address to, uint amount) validHolder public {
        require(address(this).balance >= amount);
        msg.sender.transfer(amount);
        emit TransferFunds(msg.sender, to, amount);
    }
    function walletBalance() validHolder view public returns (uint256){
        return address(this).balance;
    }  
}