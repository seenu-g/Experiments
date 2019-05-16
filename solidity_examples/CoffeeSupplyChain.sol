pragma solidity ^0.4.23;
import "./SCStorage.sol";
import "./Ownership.sol";

contract CoffeeSupplyChain is Ownership
{
  
    event CultivationStarted(address indexed user, address indexed batchNo);
    event InspectionComplete(address indexed user, address indexed batchNo);
    event HarvestComplete(address indexed user, address indexed batchNo);
    event ExportComplete(address indexed user, address indexed batchNo);
    event ImportComplete(address indexed user, address indexed batchNo);
    event ProcessComplete(address indexed user, address indexed batchNo);

    modifier isValidPerformer(address batchNo, string role) {
    
        require(keccak256(scStore.getUserRole(msg.sender)) == keccak256(role));
        require(keccak256(scStore.getNextAction(batchNo)) == keccak256(role));
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
        
    function getExporterData(address _batchNo) public view returns (uint256 quantity,
                                               string destinationAddress,string shipName,string shipNo,
                                               uint256 departureDateTime,uint256 estimateDateTime,uint256 exporterId) {
       
        (quantity,destinationAddress,shipName,shipNo,
        departureDateTime,estimateDateTime,exporterId) =  scStore.getExportData(_batchNo);  
       
        return (quantity,destinationAddress,shipName,shipNo,
                departureDateTime,estimateDateTime,exporterId);
    }
        
    function updateExporterData(address _batchNo,uint256 _quantity,    
                                string _destinationAddress,string _shipName,string _shipNo,
                                uint256 _estimateDateTime,uint256 _exporterId) 
                                public isValidPerformer(_batchNo,'EXPORTER') returns(bool) {        
        bool status = scStore.setExportData(_batchNo, _quantity, _destinationAddress, _shipName,_shipNo, _estimateDateTime,_exporterId);  
        emit ExportComplete(msg.sender, _batchNo);
        return (status);
    }
        
    function getImporterData(address _batchNo) public view returns (uint256 quantity,string shipName,
                                                string shipNo,uint256 arrivalDateTime,string transportInfo,
                                                string warehouseName,string warehouseAddress,uint256 importerId) {
        (quantity,importerId,shipName,shipNo,arrivalDateTime,
         transportInfo,warehouseName,warehouseAddress) =  scStore.getImportData(_batchNo);  
         
         return (quantity,shipName,shipNo,arrivalDateTime,
                 transportInfo,warehouseName, warehouseAddress,importerId);
    }    
    function updateImporterData(address _batchNo,
                                uint256 _quantity,string _shipName,string _shipNo,
                                string _transportInfo,string _warehouseName, string _warehouseAddress,
                                uint256 _importerId) 
                                public isValidPerformer(_batchNo,'IMPORTER') returns(bool) {
        bool status = scStore.setImportData(_batchNo, _quantity, _shipName, _shipNo, _transportInfo,_warehouseName,_warehouseAddress,_importerId);          
        emit ImportComplete(msg.sender, _batchNo);
        return (status);
    }
    
    function getProcessorData(address _batchNo) public view returns (uint256 quantity,string temperature,
                                               uint256 _rostingDuration,string _internalBatchNo,uint256 _packageDateTime,
                                               string _processorName,string _processorAddress) {
        (quantity,temperature,_rostingDuration,_internalBatchNo,
         _packageDateTime,_processorName,_processorAddress) =scStore.getProcessData(_batchNo);   
         return (quantity,temperature,_rostingDuration,_internalBatchNo,_packageDateTime,
                 _processorName,_processorAddress);
    }

    function updateProcessorData(address _batchNo,uint256 _quantity,string _temperature,
                              uint256 _rostingDuration,string _internalBatchNo,uint256 _packageDateTime,
                              string _processorName,string _processorAddress)
                              public isValidPerformer(_batchNo,'PROCESSOR') returns(bool) {
        bool status = scStore.setProcessData(_batchNo,_quantity,_temperature,_rostingDuration,
                                             _internalBatchNo,_packageDateTime,_processorName,
                                             _processorAddress);
        emit ProcessComplete(msg.sender, _batchNo);
        return (status);
    }
}