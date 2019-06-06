package sawtooth.sdk.signing;
public interface Context {
  String getAlgorithmName();

  /** Sign bytes returning a signature, hex encoded.   */
  String sign(byte[] data, PrivateKey privateKey);

  /* Verify that the private key associated with the public key, produced the signature
   * by signing the bytes.*/
  boolean verify(String signature, byte[] data, PublicKey publicKey);

  /* Get the public key from the private key.*/
  PublicKey getPublicKey(PrivateKey privateKey);

  /* Generate a random PrivateKey. */
  PrivateKey newRandomPrivateKey();

}
