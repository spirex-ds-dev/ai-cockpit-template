package fixture.app;

import fixture.core.Decision;

/** Dependency-free executable test for the app module and its core dependency. */
public final class MainTest {
    public static void main(String[] args) {
        if (!"allowed".equals(Decision.evaluate("normal work item"))) {
            throw new AssertionError("app dependency assertion failed");
        }
    }
}
