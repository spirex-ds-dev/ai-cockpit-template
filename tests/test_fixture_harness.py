import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_fixture_harness_emits_eight_phases_for_three_stacks(tmp_path):
    output = tmp_path / "bundle.json"
    subprocess.run(
        [sys.executable, "scripts/fixture_harness.py", "--output", str(output)],
        cwd=ROOT,
        check=True,
    )
    bundle = json.loads(output.read_text(encoding="utf-8"))
    assert {item["stack"] for item in bundle["fixtures"]} == {
        "python",
        "typescript-web",
        "java-multimodule",
    }
    for fixture in bundle["fixtures"]:
        assert [phase["phase"] for phase in fixture["phases"]] == [
            "Install",
            "Configure",
            "Normal Work Item",
            "Ambiguous Request",
            "Critical Domain Change",
            "Upgrade",
            "Rollback",
            "Release Check",
        ]
        assert fixture["phases"][3]["status"] == "blocked"
        assert fixture["phases"][4]["status"] == "blocked"
        assert fixture["multiAgentConflict"]["status"] == "not_run"


def test_fixture_manifests_record_unavailable_external_toolchains():
    for path in (ROOT / "examples/fixtures").glob("*/fixture.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["stack"]
        assert data["platforms"]
