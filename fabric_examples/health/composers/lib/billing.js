function SendBill(newBill) {
        var balanceDue = newBill.bill.amount;
        var ID = newBill.bill.patientID;
        
        return getParticipantRegistry('composers.participants.Patient')
            .then(function(patientRegistry) {
                  return patientRegistry.get(ID).then(function(patient){
                     patient.balanceDue += newBill.bill.amount;
                     newBill.bill.paid = false;
                     return patientRegistry.update(patient);
                })
            })
    }

    function PayBill(oldBill) {
          var ID = oldBill.bill.patientID;
          var moneyID = oldBill.bill.moneyID;
          var amt = oldBill.bill.amount;

        return getAssetRegistry('composers.billing.HospitalMoneyPool').then(function(assetRegistry) {
              return assetRegistry.get(moneyID).then(function(_moneypool){
                  _moneypool.moneypool += amt;
                  oldBill.bill.paid = true;
                  return assetRegistry.update(_moneypool);
                })
            })
            .then(function(){getParticipantRegistry('composers.participants.Patient')
                .then(function(patientRegistry) {
                    return patientRegistry.get(ID).then(function(patient){
                        patient.balanceDue -= amt;
                        oldBill.bill.paid = true;
                        return patientRegistry.update(patient);
                    })
                })
             })
             
    }
