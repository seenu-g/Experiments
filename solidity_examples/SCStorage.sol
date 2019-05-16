pragma solidity ^0.4.23;
import { SCStorageOwner } from "./SCStorageOwner.sol";

contract SCStorage is SCStorageOwner {
    address public lastAccess;
    constructor() public {
        permittedUsers[msg.sender] = 1;
        emit PermitUser(msg.sender);
    }
    event PermitUser(address caller);
    event DenyUser(address caller);
    mapping(address => uint8) permittedUsers;
    
    function grantPermission(address _caller) public onlyOwner returns(bool)
    {
        permittedUsers[_caller] = 1;
        emit PermitUser(_caller);
        return true;
    }
    function denyPermission(address _caller) public onlyOwner returns(bool)
    {
        permittedUsers[_caller] = 0;
        emit DenyUser(_caller);
        return true;
    }
    modifier onlyPermittedCaller(){
        require(permittedUsers[msg.sender] == 1,"Not Allowed");
        _;
    }
    
    struct userStruct {
        string name;
        string contactNo;
        bool isActive;
        string profileHash;
    } 
    mapping(address => userStruct) userMap;
    mapping(address => string) userRole;
    userStruct userDetail;
    function setUser(address _userAddress,string _name,string _contactNo, string _role, bool _isActive, string _profileHash) 
                     public onlyPermittedCaller returns(bool){
        userDetail.name = _name;
        userDetail.contactNo = _contactNo;
        userDetail.isActive = _isActive;
        userDetail.profileHash = _profileHash;
        
        userMap[_userAddress] = userDetail;
        userRole[_userAddress] = _role;
        return true;
    }  
    
    function getUser(address _userAddress) public onlyPermittedCaller 
                                           view returns(string name,string contactNo, 
                                           string role,bool isActive, string profileHash){
        userStruct memory tmpData = userMap[_userAddress];
        return (tmpData.name, tmpData.contactNo, userRole[_userAddress], tmpData.isActive, tmpData.profileHash);
    }
    function getUserRole(address _userAddress) public onlyPermittedCaller view returns(string)
    {
        return userRole[_userAddress];
    }

    mapping (address => string) nextAction;
    function getNextAction(address _batchNo) public onlyPermittedCaller view returns(string)
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
    basicStruct basicDetailsData;
        /*get batch basicDetails*/
    function getBasicDetails(address _batchNo) 
                             public onlyPermittedCaller view returns(string registrationNo,
                             string farmerName, string farmAddress,
                             string exporterName, string importerName) {
        
        basicStruct memory tmpData = basicMap[_batchNo];
        return (tmpData.registrationNo,tmpData.farmerName,tmpData.farmAddress,tmpData.exporterName,tmpData.importerName);
    }
    
    /*set batch basicDetails*/
    function setBasicDetails(string _registrationNo,string _farmerName,  string _farmAddress,
                             string _exporterName,string _importerName) 
                             public onlyPermittedCaller returns(address) {
        
        uint tmpData = uint(keccak256(msg.sender, now));
        address batchNo = address(tmpData);
        
        basicDetailsData.registrationNo = _registrationNo;
        basicDetailsData.farmerName = _farmerName;
        basicDetailsData.farmAddress = _farmAddress;
        basicDetailsData.exporterName = _exporterName;
        basicDetailsData.importerName = _importerName;
        
        basicMap[batchNo] = basicDetailsData;
        nextAction[batchNo] = 'FARM_INSPECTION';   
        return batchNo;
    }
    
    struct farmInspectionStruct {
        string coffeeFamily;
        string seedType;
        string fertilizerUsed;
    }
    farmInspectionStruct farmInspectionData;
    mapping (address => farmInspectionStruct) farmInspectionMap;
    function setFarmInspectionData(address batchNo,string _family,string _seedType,
                                    string _fertilizer) public onlyPermittedCaller returns(bool){
        farmInspectionData.coffeeFamily = _family;
        farmInspectionData.seedType = _seedType;
        farmInspectionData.fertilizerUsed = _fertilizer;
        
        farmInspectionMap[batchNo] = farmInspectionData;
        nextAction[batchNo] = 'HARVESTER'; 
        return true;
    }
    function getFarmInspectionData(address batchNo) public onlyPermittedCaller view returns (string coffeeFamily,string typeOfSeed,string fertilizerUsed){
        
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
                              string _humidity) public onlyPermittedCaller returns(bool){
        harvestData.cropVariety = _cropVariety;
        harvestData.temperature = _temperature;
        harvestData.humidity = _humidity;

        harvestMap[batchNo] = harvestData;
        nextAction[batchNo] = 'EXPORTER'; 
        return true;
    }
    function getHarvestData(address batchNo) public onlyPermittedCaller view returns(string cropVariety,
                                                                string temperature, string humidity){
        harvestStruct memory tmpData = harvestMap[batchNo];
        return (tmpData.cropVariety, tmpData.temperature, tmpData.humidity);
    }

    struct exportStruct {
        string destinationAddress;
        string shipName;
        string shipNo;
        uint256 quantity;
        uint256 departureDateTime;
        uint256 estimateDateTime;
        uint256 plantNo;
        uint256 exporterId;
    }
    exportStruct exportData;
    mapping (address => exportStruct) exportMap;
    function setExportData(address batchNo,uint256 _quantity,string _destinationAddress,
                              string _shipName,string _shipNo,uint256 _estimateDateTime,
                              uint256 _exporterId) public onlyPermittedCaller returns(bool){        
        exportData.quantity = _quantity;
        exportData.destinationAddress = _destinationAddress;
        exportData.shipName = _shipName;
        exportData.shipNo = _shipNo;
        exportData.departureDateTime = now;
        exportData.estimateDateTime = _estimateDateTime;
        exportData.exporterId = _exporterId;
        
        exportMap[batchNo] = exportData;
        nextAction[batchNo] = 'IMPORTER'; 
        return true;
    }
    function getExportData(address batchNo) public onlyPermittedCaller view returns(uint256 quantity,
                                                                string destinationAddress,string shipName,string shipNo,
                                                                uint256 departureDateTime, uint256 estimateDateTime,uint256 exporterId){       
        exportStruct memory tmpData = exportMap[batchNo];
        return (tmpData.quantity, tmpData.destinationAddress, tmpData.shipName, tmpData.shipNo, 
                tmpData.departureDateTime,tmpData.estimateDateTime, tmpData.exporterId);
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
    importStruct importData;
    mapping (address => importStruct) importMap;
    function setImportData(address batchNo,uint256 _quantity, 
                              string _shipName,string _shipNo,string _transportInfo,
                              string _warehouseName,string _warehouseAddress, uint256 _importerId) 
                              public onlyPermittedCaller returns(bool){
        
        importData.quantity = _quantity;
        importData.shipName = _shipName;
        importData.shipNo = _shipNo;
        importData.arrivalDateTime = now;
        importData.transportInfo = _transportInfo;
        importData.warehouseName = _warehouseName;
        importData.warehouseAddress = _warehouseAddress;
        importData.importerId = _importerId;
        
        importMap[batchNo] = importData;
        nextAction[batchNo] = 'PROCESSOR'; 
        return true;
    }
    
    function getImportData(address batchNo) 
                             public onlyPermittedCaller view returns(uint256 quantity,uint256 importerId,
                             string shipName,string shipNo,uint256 arrivalDateTime,
                             string transportInfo,string warehouseName,string warehouseAddress){
        
        importStruct memory tmpData = importMap[batchNo];
        return (tmpData.quantity,tmpData.importerId, tmpData.shipName,tmpData.shipNo,tmpData.arrivalDateTime, 
                tmpData.transportInfo,tmpData.warehouseName,tmpData.warehouseAddress);    
    }
    struct processStruct {
        uint256 quantity;
        uint256 rostingDuration;
        uint256 packageDateTime;
        string temperature;
        string internalBatchNo;
        string processorName;
        string processorAddress;
    }
    processStruct processData;
    mapping (address => processStruct) processMap;
    function setProcessData(address batchNo,uint256 _quantity,string _temperature,
                              uint256 _rostingDuration,string _internalBatchNo,uint256 _packageDateTime,
                              string _processorName,string _processorAddress) 
                              public onlyPermittedCaller returns(bool){
        processData.quantity = _quantity;
        processData.temperature = _temperature;
        processData.rostingDuration = _rostingDuration;
        processData.internalBatchNo = _internalBatchNo;
        processData.packageDateTime = _packageDateTime;
        processData.processorName = _processorName;
        processData.processorAddress = _processorAddress;

        processMap[batchNo] = processData;
        nextAction[batchNo] = 'DONE'; 
        return true;
    }

    function getProcessData( address batchNo) public onlyPermittedCaller view returns(uint256 quantity,string temperature,
                              uint256 rostingDuration, string internalBatchNo,uint256 packageDateTime,
                              string processorName,string processorAddress){

        processStruct memory tmpData = processMap[batchNo];
        return (tmpData.quantity, tmpData.temperature,tmpData.rostingDuration,tmpData.internalBatchNo, 
                tmpData.packageDateTime,tmpData.processorName,tmpData.processorAddress);
    }
}   