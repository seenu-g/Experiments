package sawtooth.sdk.signing;
import org.bitcoinj.core.Utils;

public final class Secp256k1PublicKey implements PublicKey {

  private static final String SECP256K1_ALGORITHM_NAME = "secp256k1";
  private byte[] mData;

  @Override
  public String getAlgorithmName() {
    return SECP256K1_ALGORITHM_NAME;
  }

  public Secp256k1PublicKey(final byte[] data) {
    this.mData = data;
  }

  public static Secp256k1PublicKey fromHex(final String publicKey) {
    return new Secp256k1PublicKey(Utils.HEX.decode(publicKey));
  }

  @Override
  public String hex() {
    return Utils.HEX.encode(this.mData).toLowerCase();
  }

  @Override
  public byte[] getBytes() {
    return this.mData;
  }
}