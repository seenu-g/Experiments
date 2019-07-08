function updateMedication(updateMedication){
      var id = updateMedication.patientInfo.patientID;
    return getAssetRegistry('composers.healthrecords.PatientInfo')
      .then(function(ar) {
        return ar.get(id).then(function(info){
          info.medicationArray = updateMedication.medicationArray;
          return ar.update(info);
      })
    })
  }
  
  function updatePastVisits(updatePastVisits){
    var id = updatePastVisits.patientInfo.patientID;
    return getAssetRegistry('composers.healthrecords.PatientInfo')
      .then(function(ar) {
        return ar.get(id).then(function(info){
          info.pastVisitsArray.push(updatePastVisits.newVisit);
          return ar.update(info);
      })
    })
  }
  
  function updateContact(updateContact){
    var assetRegistry;
    var id = updateContact.patient.patientID;
    return getAssetRegistry('composers.healthrecords.PatientInfo')
      .then(function(ar) {
        assetRegistry = ar;
        return assetRegistry.get(id);
      })
      .then(function(asset) {
        asset.contactDetails = updateContact.contactDetails;
        return assetRegistry.update(asset);
      });  
  }