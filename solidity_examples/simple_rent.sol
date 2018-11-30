pragma solidity ^0.5.0;
 

contract RentAgreement {
    struct RentPayment {
    uint id;
    uint value;
    string period;
    } 
    string  private house;
    address private houseOwner;
    uint256 private rentAmount;
    uint256 private ownerBalance;
    
    address private tenant;
    RentPayment[] public rentPayments;
    
    enum State {Created,Available, Occupied, Vacated}
    State private state;

    constructor( string memory _house) public {
        house = _house;
        houseOwner = msg.sender;
        state = State.Created; 
    }
    function putHouseonRent(uint256 _rent) public{
         if(msg.sender == houseOwner && state == State.Created)
         {
           rentAmount = _rent;
           state = State.Available;
         }
    }

    function getHouse() view public returns (string memory) {
        return house;
    }

    function getOwner()  view public returns (address) {
        return houseOwner;
    }

    function getTenant() view public returns (address) {
        return tenant;
    }

    function getRent()  view public returns (uint) {
        return rentAmount;
    }
    function getBalance()  view public returns (uint) {
        return ownerBalance;
    }
    function getState()  view public returns (State) {
        return state;
    }

    event contractSigned();
    event paidRent();
    event contractOver();

    function confirmAgreement()  public {
        if(msg.sender != houseOwner && state == State.Available)
        {
            emit contractSigned();
            tenant = msg.sender;
            state = State.Occupied;
        }
    }
    function payRent(uint256 _value, string memory period ) public  {
       if( _value == rentAmount && msg.sender ==  tenant && state == State.Occupied)
        {
            ownerBalance += _value;
            emit paidRent();
            rentPayments.push(RentPayment({id : rentPayments.length + 1,value : _value, period:period}));
        }
    }
    function collectRent() public {
        
      if (houseOwner == msg.sender)
      {
         ownerBalance = 0;
      }
    }
    function leaveAgreement() public {
        if(msg.sender == tenant && state == State.Occupied)
        {
            emit contractOver();
            tenant = msg.sender;
            state = State.Vacated;
        }
    }
    function AvailableForRent() public {
        if(msg.sender == houseOwner && state == State.Vacated)
        {
            tenant = msg.sender;
            state = State.Available;
            ownerBalance = 0;
            delete rentPayments;
        }   
    }
}