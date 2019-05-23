pragma solidity ^0.4.26;
contract ProductParts {
    enum Category {PART, PRODUCT}
    struct Part{
        address manufacturer;
        string serial_number;
        uint part_type;
        string creation_date;
    }

    struct Product{
        address manufacturer;
        string serial_number;
        uint product_type;
        string creation_date;
        bytes32[6] parts;
    }

    mapping(bytes32 => Part) public parts;
    mapping(bytes32 => Product) public products;
    event hashGenerated(address,string,uint8,string,bytes32);
    
    function createHash(address _address, string  s1, uint8  part_type, string  s3) private pure returns (bytes32){
           bytes32 result = keccak256(abi.encodePacked(_address,s1,part_type,s3));
           return result;
    }

    function developPart(string  serial_number, uint8  part_type, string  creation_date) public returns (bytes32){
        //Create hash for data and check if it exists. If not, create the part and return the ID to the user
       
        bytes32 part_hash = createHash(msg.sender, serial_number, part_type, creation_date); 
        emit hashGenerated(msg.sender, serial_number, part_type, creation_date,part_hash);
        require(parts[part_hash].manufacturer == address(0), "Part ID already used");

        Part memory new_part = Part(msg.sender, serial_number, part_type, creation_date);
        parts[part_hash] = new_part;
        return part_hash;
    }

    function developProduct(string serial_number, uint8 product_type, string  creation_date, bytes32[6] memory part_array) public returns (bytes32){
        uint i;
        for(i = 0;i < part_array.length; i++){
            require(parts[part_array[i]].manufacturer != address(0), "Part does not exists to be used on product");
        } 

        bytes32 product_hash = createHash(msg.sender, serial_number, product_type, creation_date);
        emit hashGenerated(msg.sender, serial_number, product_type, creation_date,product_hash);
        require(products[product_hash].manufacturer == address(0), "Product ID already used");

        Product memory new_product = Product(msg.sender, serial_number, product_type, creation_date, part_array);
        products[product_hash] = new_product; 
        return product_hash; 
    }

    function getParts(bytes32 product_hash) public view returns (bytes32[6] memory){
        require(products[product_hash].manufacturer != address(0), "Product does not exists");
        return products[product_hash].parts;
    }
}