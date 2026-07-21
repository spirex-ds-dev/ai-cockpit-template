package fixture.app;

import fixture.core.Decision;

/** Small application module proving an inter-module dependency. */
public final class Main {
    private Main() {}

    public static void main(String[] args) {
        System.out.println(Decision.evaluate("normal work item"));
    }
}
