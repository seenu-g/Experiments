pragma solidity ^0.4.25;

contract Escrow{
    
    address public buyer;
    address public seller;
    uint public price;
    
    enum  State {Started,WaitForPayment,WaitForDelivery,Complete}
    State public state;
    
    modifier currentState(State _state){require (state ==_state); _;}

    bool public buyer_in;
    bool public seller_in;
    
    constructor(address _buyer, address _seller, uint _price) public{
        
        buyer = _buyer;
        seller = _seller;
        price - _price;
    }
    // buyer and seller desposit escrow advance;
    function initiateContract() currentState(State.Started) payable external{
        require(msg.value == price);
        if(msg.sender == buyer)
         buyer_in = true;
        
        if(msg.sender == seller)
         seller_in = true;
    
        if (buyer_in == true && seller_in == true){
             state = State.WaitForPayment;
         }
    }
    
    function confirmPayment() currentState(State.WaitForPayment) payable external{
        require(msg.sender == buyer);
        require(msg.value == price);
        state = State.WaitForDelivery;
    }
    // seller gets back price and escrow advance. buyer gets back escrow advance
    function confirmDelivery() currentState(State.WaitForDelivery) payable external{
        require(msg.sender == buyer);
        require(msg.value == price);

        seller.transfer(2*price);
        buyer.transfer(price);

        state = State.Complete;
    }

}