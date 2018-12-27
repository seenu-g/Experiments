pragma solidity ^0.4.23;

/// @title Voting with delegation.
contract BoardResolutionVote {

    address public chairman;
    struct Resolution {
        bytes32 title;  
        bytes32 description;
        uint voteCount;
    }
    
    struct ShareHolder {
        uint weight; // weight is accumulated by delegation
        bool HasVoted;  
        address delegate; 
        uint8 vote;   
    }

    mapping(uint8 => Resolution) public resolutions;
    uint8 index = 0;
    mapping(address => ShareHolder) public voters;

    enum State {Init,Vote,End}
    State private agmStatus;
    
    constructor() public{
        chairman = msg.sender;
        voters[chairman].weight = 1;
        agmStatus = State.Init;
    }
    
    function addResolution(bytes32 _title, bytes32 _description) public {
     require(msg.sender == chairman);
     require(agmStatus == State.Init);
     Resolution memory resolution;
     resolution.title = _title;
     resolution.description = _description;
     resolution.voteCount = 0;
     resolutions[index]= resolution;
     index++;
    }

    function addSharedHolder(address shareholder,uint _weight) public {
        voters[shareholder].HasVoted = false;
        voters[shareholder].weight = _weight;
        voters[shareholder].HasVoted = false;
    }
    
    function startVoting() public{
        agmStatus = State.Vote;
    }
    
    function giveRightToVote(address shareholder) public {
        require(agmStatus == State.Vote);
        voters[shareholder].weight = 1;
    }

    function vote(uint8 voteStatus) public {
        ShareHolder storage sender = voters[msg.sender];
        require(!sender.HasVoted); // not yet voted
        sender.HasVoted = true;
        sender.vote = voteStatus;
        resolutions[voteStatus].voteCount += sender.weight;
    }
    
    function delegate(address to) public {

        ShareHolder storage sender = voters[msg.sender];
        require(!sender.HasVoted);            // not voted earlier
        require(voters[to].delegate != address(0));
        require(to != msg.sender);         // Self-delegation is not allowed.
        to = voters[to].delegate;

        sender.HasVoted = true;
        sender.delegate = to;
        ShareHolder storage proxyVote = voters[to];
        if (proxyVote.HasVoted) {
            resolutions[proxyVote.vote].voteCount += sender.weight;
        } else {
            proxyVote.weight += sender.weight;
        }
    }
}