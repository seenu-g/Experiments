pragma solidity ^0.4.0;
// this was used in https://remix.ethereum.org
import "browser/library.sol";

contract TestLibrary {
    using IntExtended for uint;
    
    function testIncrement(uint _base) returns (uint) {
        return IntExtended.increment(_base);
        //   return _base.increment(); // also works
    }
    
    function testDecrement(uint _base) returns (uint) {
        return IntExtended.decrement(_base);
        //        return _base.decrement(); // also works
    }
    
    function testIncrementByValue(uint _base, uint _value) returns (uint) {
        return _base.incrementByValue(_value);
    }
    
    function testDecrementByValue(uint _base, uint _value) returns (uint) {
        return _base.decrementByValue(_value);
    }
}