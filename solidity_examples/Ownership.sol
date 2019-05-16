pragma solidity ^0.4.23;

contract Ownership {
  address public owner;
  event OwnershipRenounced(address indexed previousOwner);
  event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

  constructor() public {
    owner = msg.sender;
  }
  
  modifier onlyOwner() {
    require(msg.sender == owner,"You are not the owner most possibly");
    _;
  }

  function transferOwnership(address newOwner) public onlyOwner {
    require(newOwner != address(0),"only owners can transfer ownership");
    emit OwnershipTransferred(owner, newOwner);
    owner = newOwner;
  }

  function renounceOwnership() public onlyOwner {
    emit OwnershipRenounced(owner);
    owner = address(0);
  }
}
