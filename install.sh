#!/usr/bin/env sh
set -eu

REPO="${AI_COCKPIT_TEMPLATE_REPO:-spirex-ds-dev/ai-cockpit-template}"
# This default is the published release.json tag. Candidate metadata is never
# consulted by Quick Install; use AI_COCKPIT_TEMPLATE_REF explicitly for tests.
REF="${AI_COCKPIT_TEMPLATE_REF:-v0.5.55}"
SOURCE="${AI_COCKPIT_TEMPLATE_SOURCE:-}"
EXPECTED_SHA256="${AI_COCKPIT_TEMPLATE_SHA256:-}"
METADATA_URL="${AI_COCKPIT_TEMPLATE_RELEASE_METADATA_URL:-}"

usage() {
  cat <<'USAGE'
Install AI Cockpit into the current repository.

Usage:
  ./install.sh [installer options]

Environment:
  AI_COCKPIT_TEMPLATE_SOURCE=/path/to/ai-cockpit-template
  AI_COCKPIT_TEMPLATE_REPO=spirex-ds-dev/ai-cockpit-template
  AI_COCKPIT_TEMPLATE_REF=v0.5.55
  AI_COCKPIT_TEMPLATE_SHA256=<optional assertion; release.json remains authoritative>
  AI_COCKPIT_TEMPLATE_RELEASE_DIGESTS_URL=<test-only verified manifest URL>

Common options passed through to the Python installer:
  --stack generic|rust|flutter|typescript|python|go|java|android|kotlin|swift|ruby|php|csharp
  --dry-run
  --force
  --upgrade
  --upgrade-with-active
  --replace-glossary
  --create-adoption
  --with-examples
  --update-makefile

Interactive options:
  --interactive                 Run the guided wizard.
USAGE
}

for arg in "$@"; do
  case "$arg" in
    -h|--help)
      usage
      exit 0
      ;;
  esac
done

# A no-argument TTY is the guided path. Automation without explicit options
# fails closed before cloning or touching the target repository.
if [ "$#" -eq 0 ]; then
  if [ -t 0 ]; then
    INTERACTIVE=1
  else
    echo "ERROR: no-argument install requires a TTY or explicit installer options." >&2
    exit 2
  fi
else
  INTERACTIVE=0
  if [ "$1" = "--interactive" ]; then
    INTERACTIVE=1
    shift
  fi
fi

if SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" 2>/dev/null && pwd); then
  :
else
  SCRIPT_DIR=$(pwd)
fi

if [ -z "$SOURCE" ] && [ -f "$SCRIPT_DIR/scripts/install_ai_cockpit.py" ]; then
  SOURCE="$SCRIPT_DIR"
fi

cleanup() {
  if [ "${TMPDIR_AI_COCKPIT:-}" ] && [ -d "$TMPDIR_AI_COCKPIT" ]; then
    rm -rf "$TMPDIR_AI_COCKPIT"
  fi
}
trap cleanup EXIT

if [ -z "$SOURCE" ]; then
  TMPDIR_AI_COCKPIT=$(mktemp -d)
  SOURCE="$TMPDIR_AI_COCKPIT/source"
  case "$REPO" in
    http://*|https://*|git@*)
      URL="$REPO"
      ;;
    *)
      URL="https://github.com/$REPO.git"
      ;;
  esac
  echo "Cloning AI Cockpit template from $URL at $REF"
  if ! command -v git >/dev/null 2>&1; then
    echo "ERROR: git is required for remote install." >&2
    exit 2
  fi
  git clone --depth 1 --branch "$REF" --single-branch "$URL" "$SOURCE"
  # The release contract, not a caller-provided flag, is the default trust root.
  # The optional URL override exists only for deterministic contract tests.
  if [ -n "${AI_COCKPIT_TEMPLATE_RELEASE_ASSET_URL:-}" ] && [ -n "$EXPECTED_SHA256" ]; then
    if [ -n "$METADATA_URL" ]; then
      python3 "$SOURCE/scripts/verify_quick_install_release.py" --root "$SOURCE" --ref "$REF" --asset-url "$AI_COCKPIT_TEMPLATE_RELEASE_ASSET_URL" --expected-archive-sha256 "$EXPECTED_SHA256" --metadata-url "$METADATA_URL"
    else
      python3 "$SOURCE/scripts/verify_quick_install_release.py" --root "$SOURCE" --ref "$REF" --asset-url "$AI_COCKPIT_TEMPLATE_RELEASE_ASSET_URL" --expected-archive-sha256 "$EXPECTED_SHA256"
    fi
  elif [ -n "${AI_COCKPIT_TEMPLATE_RELEASE_ASSET_URL:-}" ]; then
    if [ -n "$METADATA_URL" ]; then
      python3 "$SOURCE/scripts/verify_quick_install_release.py" --root "$SOURCE" --ref "$REF" --asset-url "$AI_COCKPIT_TEMPLATE_RELEASE_ASSET_URL" --metadata-url "$METADATA_URL"
    else
      python3 "$SOURCE/scripts/verify_quick_install_release.py" --root "$SOURCE" --ref "$REF" --asset-url "$AI_COCKPIT_TEMPLATE_RELEASE_ASSET_URL"
    fi
  elif [ -n "$EXPECTED_SHA256" ]; then
    python3 "$SOURCE/scripts/verify_quick_install_release.py" \
      --root "$SOURCE" --ref "$REF" \
      --expected-archive-sha256 "$EXPECTED_SHA256"
  else
    python3 "$SOURCE/scripts/verify_quick_install_release.py" --root "$SOURCE" --ref "$REF"
  fi
  # Release evidence is generated after the immutable source commit is selected,
  # so its authoritative copy is a release asset, not the tag-tree baseline.
  # Hydrate only the disposable clone, then let the legacy installer validate
  # the downloaded manifest's tag/source/artifact identity before target writes.
  python3 - "$SOURCE" "$REPO" "$REF" <<'PY'
import json
import pathlib
import sys
import urllib.request

source, repository, ref = map(str, sys.argv[1:])
url = __import__("os").environ.get(
    "AI_COCKPIT_TEMPLATE_RELEASE_DIGESTS_URL",
    f"https://github.com/{repository}/releases/download/{ref}/release-digests.json",
)
try:
    with urllib.request.urlopen(url, timeout=30) as response:  # nosec B310 - fixed GitHub release URL
        payload = response.read()
    manifest = json.loads(payload.decode("utf-8"))
except Exception as exc:
    raise SystemExit(f"ERROR: cannot obtain public release-digests.json: {exc}")
if not isinstance(manifest, dict) or manifest.get("releaseTag") != ref:
    raise SystemExit("ERROR: public release-digests.json does not match requested release tag")
destination = pathlib.Path(source) / ".ai" / "cockpit" / "release-digests.json"
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_bytes(payload)
PY
fi

if [ "$INTERACTIVE" -eq 1 ]; then
  exec python3 "$SOURCE/scripts/ai_install_wizard.py"
fi

exec python3 "$SOURCE/scripts/install_ai_cockpit.py" --source "$SOURCE" --target "." "$@"
