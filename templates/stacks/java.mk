# Java stack preset for AI Cockpit.
# For Spring Boot and server-side Gradle/Maven projects.
# Maven users: replace ./gradlew with mvn -q.
#   PROJECT_FORMAT_CHECK = mvn spotless:check -q
#   PROJECT_TEST         = mvn test -q
#   PROJECT_LINT         = mvn verify -q

# Declare the project's approved lane and Java major. The preset observes the
# executable selected through JAVA_HOME (when set) or AI_COCKPIT_JAVA_COMMAND;
# it never installs, switches, or mutates a JDK.
AI_COCKPIT_JAVA_LANE ?= default
AI_COCKPIT_JAVA_REQUIRED_MAJOR ?=
AI_COCKPIT_JAVA_COMMAND ?= java
AI_COCKPIT_JAVA_RUNTIME_CHECK = $(PYTHON) scripts/ai_validate_java_runtime.py --lane "$(AI_COCKPIT_JAVA_LANE)" --required-major "$(AI_COCKPIT_JAVA_REQUIRED_MAJOR)" --java-command "$(AI_COCKPIT_JAVA_COMMAND)" $(if $(JAVA_HOME),--java-home "$(JAVA_HOME)")

PROJECT_FORMAT_CHECK = $(AI_COCKPIT_JAVA_RUNTIME_CHECK) && ./gradlew spotlessCheck
PROJECT_TEST = $(AI_COCKPIT_JAVA_RUNTIME_CHECK) && ./gradlew test
PROJECT_LINT = $(AI_COCKPIT_JAVA_RUNTIME_CHECK) && ./gradlew check
