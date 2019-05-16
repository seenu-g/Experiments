pragma solidity ^0.4.23;
import { Ownership } from "./Ownership.sol";
import { SCStorage } from "./SCStorage.sol";

contract SCUser is Ownership
{
    event UserUpdate(address indexed user, string name, string contactNo, string role, bool isActive, string profileHash);
    event UserRoleUpdate(address indexed user, string role);
    
    SCStorage userStore;
    constructor(address _supplyChainAddress) public {
        userStore = SCStorage(_supplyChainAddress);
    }
    function updateUser(string _name, string _contactNo, string _role,
                        bool _isActive,string _profileHash) public returns(bool)
    {
        require(msg.sender != address(0),"the caller holds address of genesis address");
        bool status = userStore.setUser(msg.sender, _name, _contactNo, _role, _isActive,_profileHash);
        emit UserUpdate(msg.sender,_name,_contactNo,_role,_isActive,_profileHash);
        emit UserRoleUpdate(msg.sender,_role);
        return status;
    }
    function updateUserForAdmin(address _userAddress, string _name, string _contactNo, string _role,
                                bool _isActive,string _profileHash) public onlyOwner returns(bool)
    {
        require(_userAddress != address(0),"passed address is same as address of genesis address");
        bool status = userStore.setUser(_userAddress, _name, _contactNo, _role, _isActive, _profileHash);
        emit UserUpdate(_userAddress,_name,_contactNo,_role,_isActive,_profileHash);
        emit UserRoleUpdate(_userAddress,_role);
        return status;
    }
    
    function getUser(address _userAddress) public view returns(string name, string contactNo, string role, bool isActive , string profileHash){
        require(_userAddress != address(0),"not user");
        (name, contactNo, role, isActive, profileHash) = userStore.getUser(_userAddress);
       return (name, contactNo, role, isActive, profileHash);
    }
}