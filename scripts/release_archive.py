#!/usr/bin/env python3
"""Build the source-bound release archive with stable bytes across runners."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import subprocess
import tarfile
from pathlib import Path

_RUNTIME_WORKTREE_MEMBERS = (".ai/cockpit/release-digests.json",)


def _git_archive_members(root: Path, source_commit: str) -> list[tarfile.TarInfo]:
    result = subprocess.run(  # nosec B603 B607
        [
            "git",
            "-C",
            str(root),
            "archive",
            "--format=tar",
            "--prefix=ai-cockpit/",
            f"{source_commit}^{{tree}}",
        ],
        check=True,
        stdout=subprocess.PIPE,
    )
    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:") as archive:
        return archive.getmembers()


def _worktree_file_bytes(root: Path, relative_path: str) -> bytes:
    path = root / relative_path
    current = root
    for part in Path(relative_path).parts:
        current /= part
        if current.is_symlink():
            raise ValueError("archive worktree member is not a regular file")
    if not path.is_file():
        raise ValueError("archive worktree member is not a regular file")
    return path.read_bytes()


def _canonical_tar(
    root: Path, source_commit: str, *, use_worktree: bool, include_runtime_digests: bool = False
) -> bytes:
    """Serialize Git-selected paths using Python-owned stable tar metadata."""
    members = _git_archive_members(root, source_commit)
    member_names = {member.name for member in members}
    if use_worktree and include_runtime_digests:
        for relative_path in _RUNTIME_WORKTREE_MEMBERS:
            name = f"ai-cockpit/{relative_path}"
            if name not in member_names and (root / relative_path).is_file():
                members.append(tarfile.TarInfo(name))
        members.sort(key=lambda member: member.name)
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for member in members:
            stable = tarfile.TarInfo(member.name)
            stable.mode = member.mode or 0o644
            stable.type = member.type or tarfile.REGTYPE
            stable.linkname = member.linkname
            stable.uid = stable.gid = 0
            stable.uname = stable.gname = ""
            stable.mtime = 0
            if member.isfile():
                path = member.name.removeprefix("ai-cockpit/")
                if use_worktree:
                    content = _worktree_file_bytes(root, path)
                else:
                    content = subprocess.run(  # nosec B603 B607
                        ["git", "-C", str(root), "show", f"{source_commit}:{path}"],
                        check=True,
                        stdout=subprocess.PIPE,
                    ).stdout
                stable.size = len(content)
                archive.addfile(stable, io.BytesIO(content))
            else:
                stable.size = 0
                archive.addfile(stable)
    return output.getvalue()


def canonical_tar(root: Path, source_commit: str) -> bytes:
    return _canonical_tar(root, source_commit, use_worktree=False)


def canonical_tar_from_worktree(
    root: Path, source_commit: str, *, include_runtime_digests: bool = False
) -> bytes:
    """Serialize Git-selected paths using current, regular worktree bytes."""
    return _canonical_tar(
        root, source_commit, use_worktree=True, include_runtime_digests=include_runtime_digests
    )


def canonical_archive_bytes(root: Path, source_commit: str) -> bytes:
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, mode="wb", compresslevel=9, mtime=0) as compressor:
        compressor.write(canonical_tar(root, source_commit))
    return output.getvalue()


def canonical_archive_bytes_from_worktree(
    root: Path, source_commit: str, *, include_runtime_digests: bool = False
) -> bytes:
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, mode="wb", compresslevel=9, mtime=0) as compressor:
        compressor.write(
            canonical_tar_from_worktree(
                root, source_commit, include_runtime_digests=include_runtime_digests
            )
        )
    return output.getvalue()


def canonical_source_tree(root: Path, source_commit: str) -> str:
    return hashlib.sha256(canonical_tar(root, source_commit)).hexdigest()


def canonical_archive_sha(root: Path, source_commit: str) -> str:
    return hashlib.sha256(canonical_archive_bytes(root, source_commit)).hexdigest()


def canonical_source_tree_from_worktree(root: Path, source_commit: str) -> str:
    return hashlib.sha256(canonical_tar_from_worktree(root, source_commit)).hexdigest()


def canonical_archive_sha_from_worktree(root: Path, source_commit: str) -> str:
    return hashlib.sha256(canonical_archive_bytes_from_worktree(root, source_commit)).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--use-worktree",
        action="store_true",
        help="archive Git-selected paths with current regular worktree bytes",
    )
    parser.add_argument("--include-runtime-release-digests", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    archive = (
        canonical_archive_bytes_from_worktree(
            root, args.source_commit, include_runtime_digests=args.include_runtime_release_digests
        )
        if args.use_worktree
        else canonical_archive_bytes(root, args.source_commit)
    )
    args.output.write_bytes(archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
