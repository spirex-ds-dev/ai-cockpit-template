package fixture.core;

/** Deterministic policy decision shared by the fixture modules. */
public final class Decision {
    private Decision() {}

    public static String evaluate(String request) {
        if ("rocket".equals(request) || "delete all tests".equals(request)) {
            return "blocked";
        }
        return "allowed";
    }
}
