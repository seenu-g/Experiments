pragma solidity ^0.4.23;
import "./SCStorage.sol";

contract CoffeeSupplyChain 
{
  
    event CultivationStarted(address indexed user, address indexed batchNo);
    event InspectionComplete(address indexed user, address indexed batchNo);
    event HarvestComplete(address indexed user, address indexed batchNo);
    event ProcessComplete(address indexed user, address indexed batchNo);

     modifier isValidPerformer(address batchNo, string role) {
    
        require(keccak256(abi.encode(scStore.getUserRole(msg.sender))) == keccak256(abi.encode(role)));
        require(keccak256(abi.encode(scStore.getNextAction(batchNo))) == keccak256(abi.encode(role)));
        _;
    }
    
    SCStorage scStore;
    
    constructor(address _supplyChainAddress) public {
        scStore = SCStorage(_supplyChainAddress);
    }
    function getNextAction(address _batchNo) public view returns(string action)
    {
       (action) = scStore.getNextAction(_batchNo);
       return (action);
    }    
    function getBasicDetails(address _batchNo) public view returns (string registrationNo,
                                               string farmerName,string farmAddress,
                                               string exporterName,string importerName) {
        (registrationNo, farmerName, farmAddress, exporterName, importerName) = scStore.getBasicDetails(_batchNo);  
        return (registrationNo, farmerName, farmAddress, exporterName, importerName);
    }
    
    function addBasicDetails(string _registrationNo,string _farmerName,string _farmAddress,
                             string _exporterName,string _importerName
                            ) public onlyOwner returns(address) {
    
        address batchNo = scStore.setBasicDetails(_registrationNo,_farmerName,_farmAddress,
                                                            _exporterName,_importerName);
        emit CultivationStarted(msg.sender, batchNo); 
        return (batchNo);
    }                            
    
    
    function getFarmInspectorData(address _batchNo) public view returns (string coffeeFamily,
                                                    string typeOfSeed,string fertilizerUsed) {
        (coffeeFamily, typeOfSeed, fertilizerUsed) = scStore.getFarmInspectionData(_batchNo);  
        return (coffeeFamily, typeOfSeed, fertilizerUsed);
    }
        
    function updateFarmInspectorData(address _batchNo,string _coffeeFamily,
                                string _typeOfSeed,string _fertilizerUsed) 
                                public isValidPerformer(_batchNo,'FARM_INSPECTION') returns(bool) {
        bool status = scStore.setFarmInspectionData(_batchNo, _coffeeFamily, _typeOfSeed, _fertilizerUsed);  
        
        emit InspectionComplete(msg.sender, _batchNo);
        return (status);
    }
    
    function getHarvesterData(address _batchNo) public view returns (string cropVariety, 
                                                string temperatureUsed, string humidity) {
        (cropVariety, temperatureUsed, humidity) =  scStore.getHarvestData(_batchNo);  
        return (cropVariety, temperatureUsed, humidity);
    }
        
    function updateHarvesterData(address _batchNo,string _cropVariety,string 
                                _temperatureUsed,string _humidity) 
                                public isValidPerformer(_batchNo,'HARVESTER') returns(bool) {
                                    
        bool status = scStore.setHarvestData(_batchNo, _cropVariety, _temperatureUsed, _humidity);          
        emit HarvestComplete(msg.sender, _batchNo);
        return (status);
    }
}