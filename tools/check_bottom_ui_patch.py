#!/usr/bin/env python3
"""Check the UI patch against pinned Chromium plus relevant Vanadium patches."""

import argparse
import concurrent.futures
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET


REPO = Path(__file__).resolve().parents[1]
PATCHES = sorted((REPO / "patches").glob("*.patch"))


def run_git(root, *args):
    result = subprocess.run(
        ["git", "-c", f"safe.directory={root.as_posix()}", "-c", "core.longpaths=true", *args],
        cwd=root, capture_output=True, text=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)


def check(root):
    version = re.search(
        r'android_default_version_name = "([^"]+)"',
        (REPO / "vanadium/args.gn").read_text(encoding="utf-8"),
    ).group(1)
    assert PATCHES, "No UI patches found"
    entries = {}
    for patch_file in PATCHES:
        patch = patch_file.read_text(encoding="utf-8")
        for block in patch.split("diff --git ")[1:]:
            header = re.match(r"a/(\S+) b/(\S+)\n", block)
            assert header and header[1] == header[2], "Unexpected patch path"
            path = Path(header[1])
            assert path.parts[0] in ("chrome", "components") and ".." not in path.parts
            old_hash = re.search(r"\nindex ([0-9a-f]+)\.\.", block).group(1)
            # A later patch may modify a file created or changed by an earlier patch.
            entries.setdefault(header[1], old_hash)
    # Some pinned Vanadium patches restore files removed from Chromium.
    # Validate their post-Vanadium hash instead of fetching a nonexistent URL.
    restored_files = set()
    for upstream in (REPO / "vanadium/patches").glob("*.patch"):
        restored_files.update(re.findall(
            r"^diff --git a/(\S+) b/\S+\nnew file mode ",
            upstream.read_text(encoding="utf-8"), re.M))
    io_root = Path("\\\\?\\" + str(root)) if sys.platform == "win32" else root

    def fetch(entry):
        path, expected = entry
        if set(expected) == {"0"} or path in restored_files:
            return
        url = f"https://raw.githubusercontent.com/chromium/chromium/{version}/{path}"
        for attempt in range(3):
            try:
                with urllib.request.urlopen(url, timeout=60) as response:
                    data = response.read()
                break
            except Exception:
                if attempt == 2:
                    raise
        actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        assert actual.startswith(expected), f"Chromium source changed: {path} ({version})"
        target = io_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(fetch, entries.items()))

    run_git(root, "init", "-q")
    targets = set(entries)
    applied = []
    converted = root / ".git/ui-validation.patch"
    for upstream in sorted((REPO / "vanadium/patches").glob("*.patch")):
        text = upstream.read_text(encoding="utf-8")
        affected = targets.intersection(re.findall(r"^diff --git a/(\S+) b/", text, re.M))
        if not affected:
            continue
        # These are the same branding replacements performed by build.sh.
        text = text.replace("VANADIUM", "TITANIUM").replace("Vanadium", "Titanium").replace("vanadium", "titanium")
        converted.write_text(text, encoding="utf-8", newline="\n")
        run_git(root, "apply", *[f"--include={path}" for path in sorted(affected)], str(converted))
        applied.append(upstream.name)
    for path in restored_files.intersection(targets):
        expected = entries[path]
        if set(expected) != {"0"}:
            data = (io_root / path).read_bytes()
            actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            assert actual.startswith(expected), f"Vanadium-restored source changed: {path}"
    for patch_file in PATCHES:
        run_git(root, "apply", "--check", str(patch_file))
        run_git(root, "apply", str(patch_file))
    for path in targets:
        if path.endswith((".xml", ".grd")):
            ET.parse(io_root / path)
    # Reverse in a temporary index so the validated output tree stays available to tests.
    run_git(root, "add", ".")
    for patch_file in reversed(PATCHES):
        run_git(root, "apply", "--cached", "--reverse", "--check", str(patch_file))
        run_git(root, "apply", "--cached", "--reverse", str(patch_file))
    print(f"PASS: {len(PATCHES)} patches, {len(entries)} files apply to Chromium {version}; XML parses; reverse checks pass")
    print(f"Relevant Vanadium patches checked: {', '.join(applied)}")
    print(f"Patched sources: {root}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, help="Keep patched sources in a new, empty directory")
    args = parser.parse_args()
    if args.output_dir:
        root = args.output_dir.resolve()
        root.mkdir(parents=True, exist_ok=True)
        if any(root.iterdir()):
            parser.error("--output-dir must be empty")
        check(root)
    else:
        with tempfile.TemporaryDirectory(prefix="titanium-bottom-ui-") as temporary:
            check(Path(temporary))


if __name__ == "__main__":
    main()
