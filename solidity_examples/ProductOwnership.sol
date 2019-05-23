pragma solidity ^0.4.26;
import { ProductParts } from "./ProductParts.sol";
contract ProductOwnership{
    enum OperationType {PART, PRODUCT}
    mapping(bytes32 => address) public currentPartOwner;
    mapping(bytes32 => address) public currentProductOwner;

    event AssignPartOwnerEvent(bytes32 indexed p, address indexed account);
    event AssignProductOwnerEvent(bytes32 indexed p, address indexed account);
    event TransferPartEvent(bytes32 indexed p, address indexed account);
    event TransferProductEvent(bytes32 indexed p, address indexed account);
    ProductParts private pm;

    constructor(address prod_contract_addr) public {
        pm = ProductParts(prod_contract_addr);
    }

    function addOwnership(uint8 op_type, bytes32 p_hash) public returns (bool) {
        address manufacturer;
        if(op_type == uint(OperationType.PART))
        {
            (manufacturer, , , ) = pm.parts(p_hash);
        
            require(manufacturer == msg.sender, "Part was not made by requester");
            currentPartOwner[p_hash] = msg.sender;
            emit AssignPartOwnerEvent(p_hash, msg.sender);
        
        }else if (op_type == uint(OperationType.PRODUCT))
        {
            (manufacturer, , , ) = pm.products(p_hash);
        
            require(manufacturer == msg.sender, "Product was not made by requester");
            currentProductOwner[p_hash] = msg.sender;
            emit AssignProductOwnerEvent(p_hash, msg.sender);
        }
    }

    function changeOwnership(uint8 op_type, bytes32 p_hash, address to) public returns (bool) {
      //Check if the element exists and belongs to the user requesting ownership change
        if(op_type == uint(OperationType.PART)){
            require(currentPartOwner[p_hash] == msg.sender, "Part is not owned by requester");
            
            currentPartOwner[p_hash] = to;
            emit TransferPartEvent(p_hash, to);
        } else if (op_type == uint(OperationType.PRODUCT)){
            require(currentProductOwner[p_hash] == msg.sender, "Product is not owned by requester");
            
            currentProductOwner[p_hash] = to;
            emit TransferProductEvent(p_hash, to);
            
            //Change part ownership too
            bytes32[6] memory part_list = pm.getParts(p_hash);
            for(uint i = 0; i < part_list.length; i++){
                currentPartOwner[part_list[i]] = to;
                emit TransferPartEvent(part_list[i], to);
            }
        }
    }
}