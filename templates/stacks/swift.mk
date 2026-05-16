# Swift stack preset for AI Cockpit.

PROJECT_FORMAT_CHECK = swift format lint --recursive .
PROJECT_TEST = swift test
PROJECT_LINT = swift build -Xswiftc -warnings-as-errors

