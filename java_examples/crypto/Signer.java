package sawtooth.sdk.signing;

public class Signer {

  private Context mContext;
  private PrivateKey mPrivateKey;
  public Signer(final Context aContext, final PrivateKey aPrivateKey) {
    this.mContext = aContext;
    this.mPrivateKey = aPrivateKey;
  }

  public final String sign(final byte[] data) {
    return this.mContext.sign(data, this.mPrivateKey);
  }

  public final PublicKey getPublicKey() {
    return this.mContext.getPublicKey(this.mPrivateKey);
  }
}