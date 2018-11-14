pragma solidity ^0.4.0;
// run this with Current version:0.4.23+commit in https://remix.ethereum.org 
contract Assignments {
    function returnFirstValue(uint a, uint b) returns (uint) {
        return a;
    }
    
    function caller() public returns (uint) {
        return returnFirstValue({b:4, a:8});
    }
    
    function returnAllValues(uint a, uint b, uint c)  view  returns (uint, uint, uint) {
        return (a,b,c);
    }
    
    function callerAll() view public returns (uint, uint, uint) {
       uint x;
       uint y;
       uint z;
        (x,y,z) = returnAllValues(4,5,6);
        (x,y) = (y,x);
        (x,) = returnAllValues(5,10,15);
        (,z) = returnAllValues(10,20,30);
        return (x,y,z);
    }
}