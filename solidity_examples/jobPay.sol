pragma solidity ^0.4.4;

contract JobPayContract {
    address public deployer;
   
   address public employer;
   address public worker;

  uint256 public charge;

  constructor (address _employer, address _worker) public {
      
    deployer = msg.sender;
    employer = _employer;
    worker = _worker;

    charge = 0;
  }
  
 function () public payable {
    require(employer == msg.sender);
    charge += msg.value;
  }

  function payWorker() public {
    require(deployer == msg.sender);

    // transfer pay amount to tasker
    worker.transfer(charge);

    // nullify pay amount manually
    charge = 0;
  }

}
