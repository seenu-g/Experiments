  
  //function to set the entries in the block using the "SetState" function
const _setEntry = (context, address, stateValue) => {
    let dataBytes = encoder.encode(stateValue)
    let entries = {
      [address]: dataBytes 
    }
    return context.setState(entries)
  }

const voterUpload = (context, address, values) => (possibleAddressValues) => {
    let stateValueRep = possibleAddressValues[address]
  
    let voter_data = {
      name : values.name,
      id : values.id,
      password : values.password,
      station : values.station,
      voted  : false
    }
    voter_data = JSON.stringify(voter_data);
    return _setEntry(context, address, voter_data)
}
  
  const candidateUpload = (context, address, values) => (possibleAddressValues) => {
    let stateValueRep = possibleAddressValues[address]
    let candidates_data
    if(stateValueRep == null||stateValueRep == ''){
        candidates_data = {
          totalVoted:0,
          candidates:[{name:values.name,sign:values.caSign,count:0}]
        }
    }
    else{
        let getData = decoder.decode(stateValueRep)
        let parsedData = JSON.parse(getData)
        console.log("parsed data:",parsedData)
        let entry = {name:values.name,sign:values.caSign,count:0}
        parsedData['candidates'].push(entry)
        candidates_data = parsedData
    }
    candidates_data = JSON.stringify(candidates_data);
    return _setEntry(context, address, candidates_data)
  }
  
  const vote = (context, address, values) => (possibleAddressValues) => {
    let stateValueRep = possibleAddressValues[address]
  
    if (stateValueRep == null || stateValueRep == ''){
        throw new InvalidTransaction('state error')
    }
    else{
        let data = decoder.decode(stateValueRep)
        data = JSON.parse(data)
        data.totalVoted=data.totalVoted + 1
        data.candidates[values.CandidateIndex].count += 1
        let updatedData = JSON.stringify(data);
        return _setEntry(context, address, updatedData)
    }
  }
  
  const setVote = (context, address, values) => (possibleAddressValues) => {
    let stateValueRep = possibleAddressValues[address]
  
    if (stateValueRep == null || stateValueRep == ''){
        throw new InvalidTransaction('state error')
    }
    else{
        let data = decoder.decode(stateValueRep)
        data = JSON.parse(data)
        data.voted = true
        let updatedData = JSON.stringify(data);
        return _setEntry(context, address, updatedData)
    }
  }
  module.exports={voterUpload,candidateUpload,vote,setVote}