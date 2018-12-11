    pragma solidity ^0.4.23;
contract InternContract {
    struct Profile {
        string name; 
        string phone; 
        string email;
        uint date_of_birth;
        string PAN_number;
        bool Confirmed;
    }
    struct InternOffer {
        string when;
        string status;
        string duration;
        uint16 stipend;
        bool interviewComplete;
    }
    constructor() public{
        employer =  msg.sender;
    }
    address employer;
    address intern;
    mapping (string => Profile) profiles;
    mapping (string => InternOffer) interns;
    
    function setProfileData (string _name, string _phone,string _email, uint _date, string _pan) public {
        if(msg.sender == employer) 
              profiles[_pan]  = Profile({name:_name, phone:_phone, email:_email, date_of_birth:_date,PAN_number:_pan, Confirmed:false});
    }
    function getProfileData (string pan) view public  returns (string name, string phone, string email) {
        return (profiles[pan].name,profiles[pan].phone, profiles[pan].email);
    }
   
    function confirmProfile(string pan) public{
        if(msg.sender != employer) {
             intern = msg.sender;
             profiles[pan].Confirmed = true;
        }
    }
    function CallforInterview(string pan) public {
        if(msg.sender == employer && profiles[pan].Confirmed == true) 
            interns[pan] = InternOffer({when:"today",status:"Interview",duration:"",stipend:0, interviewComplete:false});
    }
    
    function setInterviewResult(string pan, string _result, string _duration, uint16 _stipend) public {
         if(msg.sender == employer && interns[pan].interviewComplete == false) {
            interns[pan].status = _result;
            interns[pan].duration = _duration;
            interns[pan].stipend = _stipend;
            interns[pan].interviewComplete = true;
         }
    }
    
    function getInterviewResult(string pan) view public returns(string duration, uint16 stipend){
        return (interns[pan].duration, interns[pan].stipend);
    }
 }