const _decodeRequest = (payload) =>
  new Promise((resolve, reject) => {
    payload = payload.toString().split(',')
    if (payload.length === 5 && payload[0]==='voter-upload') {
        console.log("Payload with voter-upload ",payload[0])
      resolve({
        action: payload[0],
        name : payload[1],
        id : payload[2],
        password : payload[3],
        station : payload[4]
      })
    }
    else if (payload.length === 4 && payload[0]==='candidate-upload') {
      console.log("Payload with candidate-upload ",payload[0])
      resolve({
        action: payload[0],
        name : payload[1],
        caSign : payload[2],
	    station : payload[3]
      })
    }
    else if (payload.length === 3 && payload[0]==='vote') {
      console.log("Payload with vote ",payload[0])
      resolve({
        action: payload[0],
        CandidateIndex : payload[1],
        station:payload[2]
      })
    }
    else if (payload.length === 2 && payload[0]==='setVote') {
      console.log("Payload with setVote ",payload[0])
      resolve({
        action: payload[0],
        voterId : payload[1]
      })
    }
    else {
      let reason = new InvalidTransaction('Invalid payload serialization')
      reject(reason)
    }
})
module.exports={_decodeRequest}