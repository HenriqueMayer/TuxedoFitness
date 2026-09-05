#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path, PurePosixPath

CANARY = 'hevy_secret_' + 'canary_7f6c9e2d3a4b5c8d'
ASSIGNMENT = re.compile(rb'(?m)^[ \t]*HEVY_API_KEY[ \t]*=[ \t]*([^\s#]+)')
HEADER_VALUE = re.compile(rb'(?i)api-key["\']?\s*[:=]\s*["\']([A-Za-z0-9_-]{20,})')
PLACEHOLDERS = (b'<', b'${', b'synthetic-', b'test-', b'example-')
MAX_BLOB_BYTES = 10 * 1024 * 1024


def secret_lines(content: bytes) -> set[int]:
    matches = []
    for pattern in (ASSIGNMENT, HEADER_VALUE):
        for match in pattern.finditer(content):
            value = match.group(1)
            if value and value not in {b'""', b"''", b'"",', b"'',"} and not value.startswith(PLACEHOLDERS):
                matches.append(match.start())
    canary = CANARY.encode()
    matches.extend(match.start() for match in re.finditer(re.escape(canary), content))
    return {content.count(b'\n', 0, position) + 1 for position in matches}


def prohibited_private_path(path: PurePosixPath) -> bool:
    text = path.as_posix().lower()
    name = path.name.lower()
    if name == '.env' or (name.startswith('.env.') and name != '.env.example'):
        return True
    if text.startswith('data/hevy/') or text.startswith('var/private/'):
        return True
    return name == 'db.sqlite3' or name.endswith(('.sqlite3', '.sqlite3-wal', '.sqlite3-shm'))


def public_worktree_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [root / name.decode() for name in result.stdout.split(b'\0') if name]


def history_objects(root: Path) -> list[tuple[str, PurePosixPath]]:
    result = subprocess.run(
        ['git', 'rev-list', '--objects', '--all'],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    objects = []
    for line in result.stdout.splitlines():
        object_id, separator, name = line.partition(' ')
        if separator and name:
            objects.append((object_id, PurePosixPath(name)))
    return objects


def blob_metadata(root: Path, object_ids: list[str]) -> dict[str, tuple[str, int]]:
    if not object_ids:
        return {}
    result = subprocess.run(
        ['git', 'cat-file', '--batch-check=%(objectname) %(objecttype) %(objectsize)'],
        cwd=root,
        check=True,
        input='\n'.join(object_ids) + '\n',
        capture_output=True,
        text=True,
    )
    metadata = {}
    for line in result.stdout.splitlines():
        object_id, object_type, size = line.split()
        metadata[object_id] = (object_type, int(size))
    return metadata


def scan_current_tree(root: Path) -> list[str]:
    findings = []
    for path in public_worktree_files(root):
        relative = PurePosixPath(path.relative_to(root).as_posix())
        if prohibited_private_path(relative):
            findings.append(f'private path is tracked: {relative}')
        if 'fixtures' in relative.parts or (
            'fixture' in relative.stem.lower()
            and relative.suffix.lower() in {'.json', '.csv', '.xpt'}
        ):
            findings.append(f'fixture review required: {relative}')
        try:
            lines = secret_lines(path.read_bytes())
        except OSError:
            continue
        findings.extend(f'secret-like value: {relative}:{line}' for line in sorted(lines))
    return findings


def scan_history(root: Path) -> list[str]:
    objects = history_objects(root)
    metadata = blob_metadata(root, list(dict.fromkeys(object_id for object_id, _ in objects)))
    findings = []
    scanned = set()
    for object_id, path in objects:
        if prohibited_private_path(path):
            findings.append(f'private path in history: {object_id[:12]}:{path}')
        object_type, size = metadata.get(object_id, ('unknown', 0))
        if object_type != 'blob' or size > MAX_BLOB_BYTES or object_id in scanned:
            continue
        scanned.add(object_id)
        content = subprocess.run(
            ['git', 'cat-file', 'blob', object_id],
            cwd=root,
            check=True,
            capture_output=True,
        ).stdout
        if secret_lines(content):
            findings.append(f'secret-like value in history: {object_id[:12]}:{path}')
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description='Scan public repository boundaries.')
    parser.add_argument('--history', action='store_true', help='scan all reachable Git objects')
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    findings = scan_current_tree(root)
    if arguments.history:
        findings.extend(scan_history(root))
    for finding in sorted(set(findings)):
        print(finding)
    if findings:
        return 1
    scope = 'Public tree and reachable history' if arguments.history else 'Public tree'
    print(f'{scope} secret and private-data scan passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
