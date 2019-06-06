package sawtooth.sdk.signing;
public interface PrivateKey {

  String getAlgorithmName();
  String hex(); //Get public key as hex
  byte[] getBytes(); // Get the byte[] underlying the PublicKey
}