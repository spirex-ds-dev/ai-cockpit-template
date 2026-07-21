package fixture.core;

/** Dependency-free executable test for the core module. */
public final class DecisionTest {
    public static void main(String[] args) {
        require("allowed".equals(Decision.evaluate("normal work item")));
        require("blocked".equals(Decision.evaluate("rocket")));
    }

    private static void require(boolean condition) {
        if (!condition) throw new AssertionError("core decision assertion failed");
    }
}
