pragma solidity ^0.4.23;

contract SCStorageOwner {
  address public owner;
  event OwnershipRenounced(address previousOwner);
  event OwnershipTransferred( address previousOwner, address  newOwner);

  constructor() public {
    owner = msg.sender;
  }
 
  function transferOwnership(address newOwner) public  {
    require(msg.sender == owner,"Not owner");
    require(newOwner != address(0),"not null address");
    address previousOwner = owner;
    owner = newOwner;
    emit OwnershipTransferred(previousOwner, newOwner);

  }

  function renounceOwnership() public  {
    require(msg.sender == owner,"Not owner");
    owner = address(0);
    emit OwnershipRenounced(owner);
  }
}
