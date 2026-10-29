#!/usr/bin/env bash
# Run INSIDE x86-64 Ubuntu, not directly on SteamOS. See docs/steam-build-handoff.md.
set -euo pipefail

resume=false
if [[ "${1:-}" == --resume ]]; then resume=true; shift; fi
if [[ $# != 1 ]]; then
    echo "Usage: bash tools/build-test-apk.sh [--resume] /absolute/build/directory" >&2
    exit 2
fi
if [[ "$(uname -s)" != Linux || "$(uname -m)" != x86_64 ]]; then
    echo 'An x86-64 Linux build environment is required.' >&2; exit 1
fi
if ! command -v apt-get >/dev/null || ! command -v sudo >/dev/null; then
    echo 'Use the Ubuntu container; do not install Chromium dependencies on SteamOS.' >&2
    exit 1
fi
source_repo="$(realpath "$(dirname "${BASH_SOURCE[0]}")/..")"
git -c safe.directory="$source_repo" -C "$source_repo" rev-parse --show-toplevel >/dev/null
build_root="$(realpath -m "$1")"
if [[ "$build_root" == / || "$build_root" == "$HOME" || "$build_root" == "$source_repo" || "$source_repo" == "$build_root/"* || "$build_root" == *' '* ]]; then
    echo 'Choose a dedicated build directory, without spaces, outside the source checkout.' >&2
    exit 1
fi
export TITANIUM_BUILD_ROOT="$build_root"
build_repo="$build_root/repo"
src="$build_repo/chromium/src"

if ! $resume; then
    if [[ -e "$build_root" && -n "$(ls -A "$build_root")" ]]; then
        echo 'Build directory must be empty. Use --resume only after preparation succeeded.' >&2
        exit 1
    fi
    if [[ -n "$(git -c safe.directory="$source_repo" -C "$source_repo" status --porcelain)" ]]; then
        echo 'Commit or preserve source changes before making the disposable build clone.' >&2
        exit 1
    fi
    mkdir -p "$build_root"
    free_kb="$(df -Pk "$build_root" | awk 'NR == 2 {print $4}')"
    if (( free_kb < 104857600 )); then
        echo 'At least 100 GiB free is required; 200 GiB or more is recommended.' >&2
        exit 1
    fi
    printf '%s\n' 'Titanium disposable test build v1' > "$build_root/.titanium-build"
    mkdir -p "$build_root/home"
    git -c safe.directory="$source_repo" clone --no-hardlinks "$source_repo" "$build_repo"
    git -C "$build_repo" checkout --detach "$(git -c safe.directory="$source_repo" -C "$source_repo" rev-parse HEAD)"
    git -C "$build_repo" submodule update --init --recursive
    if [[ "$(git -C "$build_repo/vanadium" rev-parse HEAD)" != 8ae4b1b8b014862146ff9a09dc8c6fc6e9a0a978 ]]; then
        echo 'Unexpected Vanadium revision; review the pinned build inputs before continuing.' >&2
        exit 1
    fi
    git -C "$build_repo" config user.name 'Titanium test builder'
    git -C "$build_repo" config user.email 'titanium-test@localhost'
    git -C "$build_repo" rev-parse HEAD > "$build_root/source-commit.txt"
    git -C "$build_repo" submodule status > "$build_root/submodules.txt"
    python3 "$build_repo/tools/prepare_test_build.py" "$build_repo"
    (cd "$build_repo" && bash build_test_prepare.sh) 2>&1 | tee "$build_root/prepare.log"
elif [[ ! -f "$build_root/.titanium-build" || ! -f "$build_root/prepared" || ! -f "$src/out/Default/build.ninja" ]]; then
    echo 'No fully prepared build found. Inspect prepare.log; repair the failed preparation before resuming.' >&2
    exit 1
fi

jobs="${TITANIUM_JOBS:-2}"
if [[ ! "$jobs" =~ ^[1-9][0-9]*$ ]]; then echo 'TITANIUM_JOBS must be a positive integer.' >&2; exit 2; fi
export PATH="$build_repo/depot_tools:$src/third_party/jdk/current/bin:$PATH"
(cd "$src" && autoninja -C out/Default -j "$jobs" chrome_public_apk) 2>&1 | tee -a "$build_root/compile.log"

mapfile -t apks < <(find "$src/out/Default/apks" -maxdepth 1 -type f -name 'Chrome*.apk')
if [[ ${#apks[@]} != 1 ]]; then echo 'Expected exactly one Chrome APK; inspect the build output.' >&2; exit 1; fi
sdk="$src/third_party/android_sdk/public"
aapt="$(find "$sdk/build-tools" -type f -name aapt2 | sort -V | tail -n 1)"
signer="$(find "$sdk/build-tools" -type f -name apksigner | sort -V | tail -n 1)"
if [[ -z "$aapt" || -z "$signer" ]]; then echo 'SDK verification tools missing; do not install an unverified APK.' >&2; exit 1; fi
mkdir -p "$build_root/artifacts"
"$aapt" dump badging "${apks[0]}" > "$build_root/artifacts/apk-badging.txt"
grep -q "package: name='io.github.gkoogz.titanium.test'" "$build_root/artifacts/apk-badging.txt"
grep -q "native-code:.*'arm64-v8a'" "$build_root/artifacts/apk-badging.txt"
"$signer" verify --verbose --print-certs "${apks[0]}" > "$build_root/artifacts/apk-signature.txt"
cp "${apks[0]}" "$build_root/artifacts/titanium-codex-test-arm64.apk"
cp "$build_root/source-commit.txt" "$build_root/submodules.txt" "$build_root/artifacts/"
cp "$src/out/Default/args.gn" "$build_root/artifacts/build-args.gn"
(cd "$build_root/artifacts" && sha256sum titanium-codex-test-arm64.apk > SHA256SUMS)
printf '%s\n' 'Package: io.github.gkoogz.titanium.test' 'ABI: arm64-v8a' \
    'Development/test signing; not an official release.' \
    'Full compilation succeeded. Device/UI acceptance still requires live testing.' \
    > "$build_root/artifacts/build-info.txt"
echo "Verified test APK: $build_root/artifacts/titanium-codex-test-arm64.apk"
