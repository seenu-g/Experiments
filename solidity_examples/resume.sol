pragma solidity ^0.4.25;
contract resume {

    struct Profile {
        string name; 
        string title; 
        string phone; 
        string email;
        string description;
        string panNumber;
    }
    struct Job {
        string company; 
        string Role; 
        string designation;
        string startDate; 
        string endDate; 
        string summary; 
        string highlights;
    }
    struct Education {
        string institution; 
        string degree;
        string branch;
        string startMonthYear; 
        string endMonthYear;
    }
    struct Project {
        string name; 
        string description;
    }
    struct Publication {
        string name; 
        string link; 
        string language;
    }
    struct Skill {
        string name; 
        uint32 level;
    }
    mapping (address => Profile) profiles;
    address owner;

    Project[] private projects;
    Education[] private educations;

    mapping(uint => Skill) private skills;
    uint32 public skillCount;
    
    mapping(uint => Publication) publications;
    uint32 public pubCount;
    
    constructor() public{
        owner =  msg.sender;
        skillCount = 0;
        pubCount = 0;
    }

    modifier onlyOwner {
        require(msg.sender == owner);
        _;
    }

    function setProfile(string _name, string _title, string _phone, string _email, string _description, string _panNumber) public onlyOwner() {
        Profile storage selfProfile = profiles[owner];
        selfProfile.name = _name;
        selfProfile.title = _title;
        selfProfile.phone = _phone;
        selfProfile.description = _description;
        selfProfile.panNumber = _panNumber;
        selfProfile.email = _email;
    }
    
    function getProfile(address ins) view public returns (string, string, string,string,string,string) {
        return (profiles[ins].name, profiles[ins].title, profiles[ins].phone,profiles[ins].email,profiles[ins].description,profiles[ins].panNumber);
    }

    // operation = 0 maps to delete and 1 maps to add
    function addEducation (bool operation, string _institution,string _degree, string _branch,string _startMonthYear,string _endMonthYear) public onlyOwner() {
        if (operation) {
            educations.push(Education(_institution,_degree,_branch,_startMonthYear,_endMonthYear));
        }
    }
    function getEducationCount() view public returns(uint){
        return educations.length;
    }
    function getEducation(uint8 index) view public returns(string,string,string,string,string){
        return (educations[index].institution,educations[index].degree,educations[index].branch,educations[index].startMonthYear,educations[index].endMonthYear);
    }
    function addSkill(bool operation, string _name, uint32 _level) public onlyOwner() returns (uint32) {
        if (operation) {
          Skill storage skill = skills[skillCount];
          skill.name = _name;
          skill.level = _level;
          skillCount++;         
        } 
        return skillCount;
    }
   
    function getSkill(uint32 index) view public returns(string,uint32){
          return (skills[index-1].name,skills[index-1].level);
    }
    function addPublication (bool operation, string _name, string _link, string _language) public onlyOwner() returns(uint32) {
        if (operation) {
          Publication storage publication = publications[pubCount];
          publication.name = _name;
          publication.link = _link;
          publication.language = _language;
          pubCount++;   
        } 
        return pubCount;
    }
   
    function getPublication(uint32 index) view public returns(string,string,string){
        return (publications[index-1].name, publications[index-1].link, publications[index-1].language);
    }
  
}