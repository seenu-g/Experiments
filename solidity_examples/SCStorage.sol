pragma solidity ^0.4.23;
contract SCStorage {
    constructor() public {

    }
    
    struct userStruct {
        string name;
        string contactNo;
        bool isActive;
        string profileHash;
    } 
    mapping(address => userStruct) userMap;
    mapping(address => string) userRole;
    function setUser(address _userAddress,string _name,string _contactNo, string _role, bool _isActive, string _profileHash) 
                     public  returns(bool){
        userMap[_userAddress] = userStruct(_name,_contactNo,_isActive,_profileHash);
        userRole[_userAddress] = _role;
        return true;
    }
    
    function getUser(address _userAddress) public  
                                           view returns(string name,string contactNo,
                                           string role,bool isActive, string profileHash){
        return (userMap[_userAddress].name, userMap[_userAddress].contactNo, userRole[_userAddress],
                userMap[_userAddress].isActive, userMap[_userAddress].profileHash);
    }
    function getUserRole(address _userAddress) public  view returns(string)
    {
        return userRole[_userAddress];
    }

    mapping (address => string) nextAction;
    function getNextAction(address _batchNo) public  view returns(string)
    {
        return nextAction[_batchNo];
    }
    
        struct basicStruct {
        string registrationNo;
        string farmerName;
        string farmAddress;
        string exporterName;
        string importerName;
    }
    mapping (address => basicStruct) basicMap;
    function setBasicDetails(string _registrationNo,string _farmerName,  string _farmAddress,
                             string _exporterName,string _importerName)
                             public  returns(address) {
        
        uint tmpData = uint(keccak256(msg.sender, now));
        address batchNo = address(tmpData);
        
        basicMap[batchNo] = basicStruct(_registrationNo,_farmerName,_farmAddress,_exporterName,_importerName);
        nextAction[batchNo] = 'FARM_INSPECT';
        return batchNo;
    }
    function getBasicDetails(address _batchNo)
                             public  view returns(string registrationNo,
                             string farmerName, string farmAddress,
                             string exporterName, string importerName) {
        
        return (basicMap[_batchNo].registrationNo,basicMap[_batchNo].farmerName,basicMap[_batchNo].farmAddress,
                basicMap[_batchNo].exporterName,basicMap[_batchNo].importerName);
    }
    
    struct farmInspectionStruct {
        string coffeeFamily;
        string seedType;
        string fertilizerUsed;
    }
    mapping (address => farmInspectionStruct) farmInspectionMap;
    function setFarmInspectionData(address batchNo,string _family,string _seedType,
                                    string _fertilizer) public returns(bool){
        farmInspectionMap[batchNo] = farmInspectionStruct(_family,_seedType,_fertilizer);
        nextAction[batchNo] = 'HARVEST'; 
        return true;
    }
    function getFarmInspectionData(address batchNo) public  view returns (string coffeeFamily,string typeOfSeed,string fertilizerUsed){
        
        farmInspectionStruct memory tmpData = farmInspectionMap[batchNo];
        return (tmpData.coffeeFamily, tmpData.seedType, tmpData.fertilizerUsed);
    }
    
    struct harvestStruct {
        string cropVariety;
        string temperature;
        string humidity;
    }    
    harvestStruct harvestData;
    mapping (address => harvestStruct) harvestMap;
    function setHarvestData(address batchNo, string _cropVariety,string _temperature,
                              string _humidity) public  returns(bool){
        harvestMap[batchNo] = harvestStruct(_cropVariety,_temperature,_humidity);
        nextAction[batchNo] = 'EXPORT'; 
        return true;
    }
    function getHarvestData(address batchNo) public  view returns(string cropVariety,
                                                                string temperature, string humidity){
        return (harvestMap[batchNo].cropVariety, harvestMap[batchNo].temperature, harvestMap[batchNo].humidity);
    }
    
     struct exporterStruct {
        string destinationAddress;
        string shipName;
        string shipNo;
        uint256 quantity;
        uint256 departureDateTime;
        uint256 estimateDateTime;
        uint256 plantNo;
        uint256 exporterId;
    }
    mapping (address => exporterStruct) exportMap;
    function getExportData(address batchNo) public view returns(uint256 quantity,
                                            string destinationAddress,string shipName,string shipNo,
                                             uint256 plantNo,uint256 exporterId){
        return (exportMap[batchNo].quantity,exportMap[batchNo].destinationAddress,
                exportMap[batchNo].shipName, exportMap[batchNo].shipNo,
                exportMap[batchNo].plantNo, exportMap[batchNo].exporterId);
    }
    struct importStruct {
        uint256 quantity;
        uint256 arrivalDateTime;
        uint256 importerId;
        string shipName;
        string shipNo;
        string transportInfo;
        string warehouseName;
        string warehouseAddress;
    }
    mapping (address => importStruct) importMap;
    struct processStruct {
        uint256 quantity;
        uint256 rostingDuration;
        uint256 packageDateTime;
        string temperature;
        string internalBatchNo;
        string processorName;
        string processorAddress;
    }
    mapping (address => processStruct) processMap;
}