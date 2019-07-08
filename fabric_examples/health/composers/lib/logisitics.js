function addAppointment(addAppointment){
	var assetRegistry;
	var id = addAppointment.appointment.appointmentID;
	return getAssetRegistry('composers.logistics.Appointment')
		.then(function(ar){
			assetRegistry = ar;
			return assetRegistry.get(id);
		})
		.then(function(asset){
			asset.time = addAppointment.time;
			asset.realTime = addAppointment.realTime;
			return assetRegistry.update(asset);
		})
}

function onChangeAssetValue(changeAssetValue) {
    var assetRegistry;
    var id = changeAssetValue.relatedAsset.assetId;
    return getAssetRegistry('org.india.biznet.SampleAsset')
        .then(function(ar) {
            assetRegistry = ar;
            return assetRegistry.get(id);
        })
        .then(function(asset) {
            asset.value = changeAssetValue.newValue;
            return assetRegistry.update(asset);
        });
}
