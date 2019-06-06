package sawtooth.sdk.signing;

public final class CryptoFactory {

  /* Private constructor for Factory class. */
  private CryptoFactory() { }

  public static Context createContext(final String algorithmName) {

    Context context = null;

    if (algorithmName.equals("secp256k1")) {
      context = new Secp256k1Context();
    } else {
      throw new RuntimeException("During call to createContext, Algorithm is not implemented");
    }

    return context;
  }

}