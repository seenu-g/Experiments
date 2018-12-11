pragma solidity ^0.4.18;
// a mapping is referred to a hash table, which consists of key types and value type pairs
// you currently cannot return a mapping like owners or iterate through
contract FileRegistry 
{ 
    struct FileMapping 
    { 
        uint timestamp; 
        string owner; 
    } 

    mapping (string => FileMapping) files; 
    string[] private owners;

    event FileLogStatus(bool status, uint timestamp, string owner, string fileHash); 

    function set(string owner, string fileHash) public
    { 
        if(files[fileHash].timestamp == 0) 
        { 
            files[fileHash] = FileMapping(block.timestamp, owner); 
            FileLogStatus(true, block.timestamp, owner, fileHash); 
            owners.push(owner); 
        } 
        else 
        { 
            FileLogStatus(false, block.timestamp, owner, fileHash); 
        } 
    } 
    function get(string fileHash) public view returns (uint timestamp, string owner) 
    { 
        return (files[fileHash].timestamp, files[fileHash].owner); 
    } 

} 
