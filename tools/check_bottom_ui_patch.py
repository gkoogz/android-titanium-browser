#!/usr/bin/env python3
"""Check the UI patch against pinned Chromium plus relevant Vanadium patches."""

import argparse
import concurrent.futures
import hashlib
from pathlib import Path
import re
import subprocess
import tempfile
import urllib.request
import xml.etree.ElementTree as ET


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "patches/0001-complete-bottom-address-bar-and-tab-cards.patch"


def run_git(root, *args):
    subprocess.run(
        ["git", "-c", f"safe.directory={root.as_posix()}", "-c", "core.longpaths=true", *args],
        cwd=root, check=True, capture_output=True, text=True,
    )


def check(root):
    version = re.search(
        r'android_default_version_name = "([^"]+)"',
        (REPO / "vanadium/args.gn").read_text(encoding="utf-8"),
    ).group(1)
    patch = PATCH.read_text(encoding="utf-8")
    entries = []
    for block in patch.split("diff --git ")[1:]:
        header = re.match(r"a/(\S+) b/(\S+)\n", block)
        assert header and header[1] == header[2], "Unexpected patch path"
        path = Path(header[1])
        assert header[1].startswith("chrome/") and ".." not in path.parts
        old_hash = re.search(r"\nindex ([0-9a-f]+)\.\.", block).group(1)
        entries.append((header[1], old_hash))

    def fetch(entry):
        path, expected = entry
        if set(expected) == {"0"}:
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
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(fetch, entries))

    run_git(root, "init", "-q")
    targets = {path for path, _ in entries}
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
    run_git(root, "apply", "--check", str(PATCH))
    run_git(root, "apply", str(PATCH))
    for path in targets:
        if path.endswith((".xml", ".grd")):
            ET.parse(root / path)
    run_git(root, "apply", "--reverse", "--check", str(PATCH))
    print(f"PASS: {len(entries)} files apply to Chromium {version}; XML parses; reverse check passes")
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
