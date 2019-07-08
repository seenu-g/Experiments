function CastVote(vote) {
  var voter = vote.voter;
  var candidate = vote.candidate;
  if (voter.voted) {
    throw new Error('Already voted');
  }
  candidate.votes += 1;
  return getAssetRegistry('org.acme.votenetwork.Candidate').then(function(CandidateRegistry) {
    getParticipantRegistry('org.acme.votenetwork.Voter').then(function(participantRegistry) {
      voter.voted = true;
      return participantRegistry.update(voter);
    }).catch(function(error) {
      // Add optional error handling here.
    });
    return CandidateRegistry.update(candidate);
  });
}