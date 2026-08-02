"""Human-readable presentation of a read-only installer plan."""

from installer.planning import InstallationPlan


def render_plan(plan: InstallationPlan) -> str:
    actions = "\n".join(f"- {action}" for action in plan.actions) or "- no changes proposed"
    return f"Installation plan for {plan.target}:\n{actions}\n"
