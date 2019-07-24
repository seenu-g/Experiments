  pragma solidity ^0.4.23;
contract HelloWorldContract {
  event Hi();
  function sayHi() public view returns (string){
    emit Hi();
    return 'Hello World';
  }
}