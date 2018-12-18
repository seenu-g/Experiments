pragma solidity ^0.4.23;

contract MultiPartyWallet {

    address private regulator;
    mapping(address => uint8) private particpants;

    uint constant MIN_SIGNATURES = 2;
    uint private _index; // transaction index

    struct Transaction {
      address from;
      address to;
      uint amount;
      uint8 signatureCount;
      mapping (address => uint8) signatures;
    }

    mapping (uint => Transaction) private _transactions;
    uint[] private _pendingTransactions;

    modifier isRegulator() {
        require(msg.sender == regulator);
        _;
    }

    modifier validMember() {
        require(msg.sender == regulator || particpants[msg.sender] == 1);
        _;
    }

    event DepositEvent(address from, uint amount);
    event TransactionCreatedEvent(address from, address to, uint amount, uint transactionId);
    event TransactionCompletedEvent(address from, address to, uint amount, uint transactionId);
    event TransactionSignedEvent(address by, uint transactionId);

    constructor()  public {
        regulator = msg.sender;
    }

    function addOwner(address participant) isRegulator public {
        particpants[participant] = 1;
    }

    function removeOwner(address participant) isRegulator public {
        particpants[participant] = 0;
    }

    function deposit() public payable {
        emit DepositEvent(msg.sender, msg.value);
    }

    function withdraw(uint amount)  public {
        transferTo(msg.sender, amount);
    }

    function transferTo(address to, uint amount) validMember public {
        require(address(this).balance >= amount);
        uint transactionId = _index++;

        Transaction memory temptransaction;
        temptransaction.from = msg.sender;
        temptransaction.to = to;
        temptransaction.amount = amount;
        temptransaction.signatureCount = 0;

        _transactions[transactionId] = temptransaction;
        _pendingTransactions.push(transactionId);

        emit TransactionCreatedEvent(msg.sender, to, amount, transactionId);
    }

    function getPendingTransactions() view validMember public returns (uint[]) {
      return _pendingTransactions;
    }

    function signTransaction(uint transactionId) validMember public {

      Transaction storage transaction = _transactions[transactionId];

      // Transaction must exist
      require(0x0 != transaction.from);
      // Creator cannot sign the transaction
      require(msg.sender != transaction.from);
      // Cannot sign a transaction more than once
      require(transaction.signatures[msg.sender] != 1);

      transaction.signatures[msg.sender] = 1;
      transaction.signatureCount++;

      emit TransactionSignedEvent(msg.sender, transactionId);

      if (transaction.signatureCount >= MIN_SIGNATURES) {
        require(address(this).balance >= transaction.amount);
        transaction.to.transfer(transaction.amount);
        emit TransactionCompletedEvent(transaction.from, transaction.to, transaction.amount, transactionId);
        deleteTransaction(transactionId);
      }
    }

    function deleteTransaction(uint transactionId) validMember private {
      uint8 replace = 0;
      for(uint i = 0; i < _pendingTransactions.length; i++) {
        if (1 == replace) {
          _pendingTransactions[i-1] = _pendingTransactions[i];
        } else if (transactionId == _pendingTransactions[i]) {
          replace = 1;
        }
      }
      delete _pendingTransactions[_pendingTransactions.length - 1];
      _pendingTransactions.length--;
      delete _transactions[transactionId];
    }

    function walletBalance() constant public returns (uint) {
      return address(this).balance;
    }
}