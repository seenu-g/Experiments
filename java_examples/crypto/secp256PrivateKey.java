package sawtooth.sdk.signing;


import org.bitcoinj.core.Utils;

public final class Secp256k1PrivateKey implements PrivateKey {

  private static final String SECP256K1_ALGORITHM_NAME = "secp256k1";

  private byte[] mPrivKey;

  @Override
  public String getAlgorithmName() {
    return SECP256K1_ALGORITHM_NAME;
  }

  public Secp256k1PrivateKey(final byte[] data) {
    this.mPrivKey = data;
  }

  /**
   * Create a private key from hex. */
  
  public static Secp256k1PrivateKey fromHex(final String aPrivateKey) {
    return new Secp256k1PrivateKey(Utils.HEX.decode(aPrivateKey));
  }

  @Override
  public String hex() {
    return Utils.HEX.encode(this.mPrivKey).toLowerCase();
  }

  @Override
  public byte[] getBytes() {
    return this.mPrivKey;
  }
}
