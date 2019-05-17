pragma solidity ^0.4.26;
contract ProductParts {
    struct Part{
        address manufacturer;
        string serial_number;
        string part_type;
        string creation_date;
    }

    struct Product{
        address manufacturer;
        string serial_number;
        string product_type;
        string creation_date;
        bytes32[6] parts;
    }

    mapping(bytes32 => Part) public parts;
    mapping(bytes32 => Product) public products;
    
    function createHash(address a1, string memory s1, string memory s2, string memory s3) private pure returns (bytes32){
        bytes20 b_a1 = bytes20(a1);
        bytes memory b_s1 = bytes(s1);
        bytes memory b_s2 = bytes(s2);
        bytes memory b_s3 = bytes(s3);

        //Then calculate and reserve a space for the full string
        string memory s_full = new string(b_a1.length + b_s1.length + b_s2.length + b_s3.length);
        bytes memory b_full = bytes(s_full);
        uint j = 0;
        uint i;
        for(i = 0; i < b_a1.length; i++){
            b_full[j++] = b_a1[i];
        }
        for(i = 0; i < b_s1.length; i++){
            b_full[j++] = b_s1[i];
        }
        for(i = 0; i < b_s2.length; i++){
            b_full[j++] = b_s2[i];
        }
        for(i = 0; i < b_s3.length; i++){
            b_full[j++] = b_s3[i];
        }

        //Hash the result and return
        return keccak256(b_full);
    }

    function developPart(string  serial_number, string  part_type, string  creation_date) public returns (bytes32){
        //Create hash for data and check if it exists. If not, create the part and return the ID to the user
       
        bytes32 part_hash = createHash(msg.sender, serial_number, part_type, creation_date);
        Part memory new_part = Part(msg.sender, serial_number, part_type, creation_date);
        parts[part_hash] = new_part;
        return part_hash;
    }

    function developProduct(string serial_number, string product_type, string  creation_date, bytes32[6] memory part_array) public returns (bytes32){
        //Check whether all the parts exist. if yes,hash values and add to product mapping.
        uint i;
        for(i = 0;i < part_array.length; i++){
            require(parts[part_array[i]].manufacturer != address(0), "Parts needs to have valid manufacturer");
        }

        bytes32 product_hash = createHash(msg.sender, serial_number, product_type, creation_date);
        Product memory new_product = Product(msg.sender, serial_number, product_type, creation_date, part_array);
        products[product_hash] = new_product;
        return product_hash;
    }

    function getParts(bytes32 product_hash) public view returns (bytes32[6] memory){
        require(products[product_hash].manufacturer != address(0), "Product inexistent");
        return products[product_hash].parts;
    }
}