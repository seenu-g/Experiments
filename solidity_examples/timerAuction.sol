pragma solidity ^0.4.25;
interface Auction{
    function bid() payable  external;
    function end()  external;
}

contract BaseAuction is Auction{
    address public owner;
    event AuctionComplete( address _winner, uint _bid);
    constructor() public{
        owner = msg.sender;
    }
    modifier ownerOnly{
        require(msg.sender == owner);
        _;
    }
}
contract TimerAuction is BaseAuction{
   string public item;
   uint public auctionEnds;
   uint public maxBid;
   address public maxBidder;
   bool ended;
   mapping(address=>uint) pendingWithdrawls;
   
   event BidAccepted(address _bidder, uint _bid);
   
   constructor(string _item, uint _durationMinutes) public{
       item = _item;
       auctionEnds = now + (_durationMinutes * 1 minutes);
   }
   
   function bid() external payable {
       require(now <auctionEnds);
       require(msg.value > maxBid);
       
       if (maxBidder!=0) {
           //maxBidder.transfer(maxBid);
           pendingWithdrawls[msg.sender] += maxBid;
       }
       
       maxBidder = msg.sender;
       maxBid = msg.value;
       emit BidAccepted(maxBidder,maxBid);
   }
   
   function withdraw() public returns(bool){
     uint amount = pendingWithdrawls[msg.sender];
     if(amount >0){
         pendingWithdrawls[msg.sender] =0;
         if(!msg.sender.send(amount)){
              pendingWithdrawls[msg.sender] = amount;
              return false;
         }
     }
      return true;
   }
   function end()  public ownerOnly{
       require(now >= auctionEnds);
       require(!ended);
       ended = true;
       emit AuctionComplete(maxBidder,maxBid);
       
       //owner.transfer(maxBid);
       pendingWithdrawls[owner]+= maxBid; // owner also needs to withdraw DIY
   }
}