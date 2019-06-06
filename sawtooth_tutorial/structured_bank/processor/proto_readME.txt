Change 1 : handler.js
var protos = require("./../shared/structuredBank")
const { protobuf1 } = require('./payload');
var protobuf = require("protobufjs");

Change 2 : handler.js
Replace  with following statements in function apply(transactionProcessRequest, state) 

 if (parameters.action == protos.structuredBankPackage.PayLoad.Action.CREATE_ACCOUNT) {
            var temp = parameters.createAccount;
            console.log("parameters", temp.customerId, temp.customerName, temp.savingsBalance, temp.checkingBalance)
            return this.create_account(state, temp.customerId, temp.customerName, temp.savingsBalance, temp.checkingBalance)
} else if (parameters.action == protos.structuredBankPackage.PayLoad.Action.DEPOSIT_MONEY) {
            var temp = parameters.depositMoney;
            console.log("deposit", temp.customerId, temp.amount)
            return this.deposit_money(temp.customerId, temp.amount, state)
} else if (parameters.action == protos.structuredBankPackage.PayLoad.Action.WITHDRAW_MONEY) {
            var temp = parameters.withdrawMoney;
            return this.withdraw_money(temp.customerId, temp.amount, state)
} else if (parameters.action == protos.structuredBankPackage.PayLoad.Action.TRANSFER_MONEY) {
            var temp = parameters.transferMoney
            return this.transfer_money(temp.sourceCustomerId, temp.destCustomerId, temp.amount, state)