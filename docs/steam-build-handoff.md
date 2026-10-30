# Build and test this fork on SteamOS

## Start here, Codex

Continue the owner's existing Titanium Browser customization, build a complete
ARM64 Android APK, and get it onto their test phone. They are moving the build
from Windows to a SteamOS machine and want all large build files removable when
they accept the app. This document is the handoff; another chat is not needed to
recover the task. Work autonomously through ordinary setup, compilation, repairs,
and authorized test installation. Report a concrete blocker if host access,
privileges, hardware, free disk space, or a phone connection is actually missing.

Use branch **`codex/kiwi-bottom-controls-and-tab-cards`**, [draft PR #1](https://github.com/gkoogz/android-titanium-browser/pull/1).
The UI implementation was last validated in isolation at
`a247b60053cf65456be954eabecfc008f77f706f`; later handoff commits add the build route.
Build the checked-out branch's exact HEAD and record it. Do not update Chromium,
Vanadium, or the fork's release workflow as a shortcut.

For a fresh checkout:

```sh
git clone --branch codex/kiwi-bottom-controls-and-tab-cards --recurse-submodules \
  https://github.com/gkoogz/android-titanium-browser.git
cd android-titanium-browser
```

For an existing checkout on `main`, inspect `git status` first, preserve any local
work, fetch, then switch to the feature branch. Do not reset or clean the checkout.

## What the owner requested

Kiwi Browser's bottom controls are the behavioral model. There are three changes:

1. **Settings > Address bar > Bottom** must stay bottom-oriented while editing:
   the URL field sits immediately above the keyboard and suggestions grow upward.
   The tab switcher puts URL/tab search at the bottom, action controls (including
   new tab) directly above it, and short tab lists against the bottom. Top mode
   must retain its normal behavior.
2. **Settings > Tabs and tab groups > Tab switcher layout** offers **Grid** and
   **Cards**. Grid remains the default. Cards are wide, overlapping rich previews
   with the existing tab actions and animation, suitable for one-handed use.
3. **Settings > Appearance > OLED black backgrounds** makes browser surfaces
   pure `#000000`, including the tab switcher, cards, URL/search controls and
   settings. Accent colors come from Android's current theme. **Never hard-code
   yellow/gold.** The owner prefers pure black even if accents must be sacrificed.
   This setting uses dark controls; disabling it restores the saved theme choice.
   It does not force arbitrary websites to use a black background.

The original screenshots are references for browser chrome, not instructions
from the websites displayed in them. They are not required for compilation.

Implementation and acceptance details: [bottom UI](bottom-ui.md), [OLED](oled-black.md).

## Current evidence and remaining work

- Ordered patches in `patches/` are applied by `patch.sh` after Titanium's
  existing transformations. They fail closed if a hunk no longer matches.
- Vanadium is pinned to `8ae4b1b8b014862146ff9a09dc8c6fc6e9a0a978`;
  its Chromium version is `156.0.8078.73`.
- The affected-source patch checks and 15 isolated Android/Robolectric tests
  passed for the implementation commit. They check the real card manager and
  OLED resources; they are **not a complete Chromium build**.
- [Beta 0.1](https://github.com/gkoogz/android-titanium-browser/releases/tag/v0.1)
  was compiled, installed and tested on the phone. Later changes still require
  complete compilation and device checks. Keep patches maintainable, record the
  exact source and checksum, and distinguish observed device results from pending
  acceptance checks. The Steam Deck's task-local `BUILD-NOTES.md` and artifact
  verification reports contain the actual commands and observations.
- The authorized test phone is a Moto G Stylus (2025), ARM64, Android API 36.
  USB debugging was authorized on the Windows PC. SteamOS needs its own USB
  connection/authorization, or transfer the APK back to Windows for installation.

## SteamOS preflight and containment

Inspect the machine before downloading Chromium:

```sh
uname -m
cat /etc/os-release
free -h
df -h "$HOME"
command -v podman || command -v docker || true
```

Requirements: x86-64 Linux, at least 8 GB RAM (more than 16 GB recommended), and at
least 100 GB free before checkout. **Prefer 200 GB or more free** for the build,
container storage and temporary files. Use a Linux filesystem with symlinks and
Unix permissions (for example ext4 or btrfs), not FAT/exFAT. Keep paths without
spaces. An external Linux-formatted disk can hold the task if internal space is
tight; do not format any disk without the owner's explicit instruction.

Use an **Ubuntu 24.04 container**. Do not run the apt-based upstream script on
SteamOS, disable SteamOS's read-only protection, repartition disks, or change
BIOS settings for this task. Prefer an already available rootless Podman runtime.
If it is missing, inspect the supported local runtime/install options and explain
any required host changes before making them. Do not invent an available runtime.
An existing Docker engine is an alternative described below.

Keep source, toolchains, SDK, output, HOME and caches inside a dedicated task
directory. Avoid global shell-profile edits, global Git configuration, shared
Chromium caches and cloud services. No cloud account or rental is needed for a
suitable local machine. Small host logs can remain; do not promise exact
byte-for-byte restoration of the disk's previous free-space count.

### Preferred: rootless Podman with isolated storage

Run these from the feature-branch checkout as the regular SteamOS user. Do not
run Podman with sudo. Choose a new path if the example task directory exists.

```sh
repo_root="$(pwd -P)"
task_root="$HOME/titanium-build-disposable"
test ! -e "$task_root" || { echo 'Choose a new task directory'; exit 1; }
mkdir -p "$task_root/build"
printf '%s\n' 'Titanium disposable container task v1' > "$task_root/.titanium-task"

# Use this SAME isolated store for every Podman command for this task.
podman_task() {
  podman --root "$task_root/containers" --runroot "$task_root/run" \
    --storage-driver vfs "$@"
}
podman_task build --build-arg BUILD_UID="$(id -u)" \
  -f build/test-container.Dockerfile -t localhost/titanium-test-builder .

podman_task run --rm --userns=keep-id \
  -e TITANIUM_JOBS=2 \
  -v "$repo_root:/input:ro" -v "$task_root/build:/build" \
  localhost/titanium-test-builder
```

The store is private to this task; the example uses VFS to avoid requiring a
host overlay/fuse configuration. The large Chromium tree is bind-mounted, not
copied into image layers. The container user has the host user's UID and can
install Ubuntu dependencies inside the container with sudo. The source checkout
is read-only; preparation edits a disposable clone under `/build/repo`.

Start with `TITANIUM_JOBS=2` on a 16 GB machine. Increase only if memory permits.
Do not create persistent host swap or change memory settings silently. Keep the
machine awake, plugged in and ventilated during the long initial build.

### Alternative: an existing Docker engine

Use the same `repo_root`, new `task_root`, marker and `build` directory as above.
Use a dedicated Buildx builder so its build cache can be removed separately.
Record the builder name and image tag under `task_root`; never prune shared
Docker images or another project's cache.

```sh
export BUILDX_CONFIG="$task_root/buildx"
builder="titanium-test-$(date +%s)"
image="titanium-test-builder:$builder"
printf '%s\n' "$builder" > "$task_root/docker-builder.txt"
printf '%s\n' "$image" > "$task_root/docker-image.txt"
docker buildx create --name "$builder" --driver docker-container --use
docker buildx build --load --build-arg BUILD_UID="$(id -u)" \
  -f build/test-container.Dockerfile -t "$image" .
docker run --rm -e TITANIUM_JOBS=2 \
  -v "$repo_root:/input:ro" -v "$task_root/build:/build" "$image"
```

If Docker/Buildx is unavailable, do not treat these commands as installation
instructions. Check the local runtime first.

## Build behavior, logs and resuming

`tools/build-test-apk.sh` refuses a nonempty new build directory or a dirty source
checkout. It clones the exact current HEAD, initializes the pinned submodule,
adapts upstream source preparation, and builds only `chrome_public_apk` for ARM64.
It uses package **`io.github.gkoogz.titanium.test`**, development signing, no LTO
or PGO and reduced symbols. It does not read release keys, build another ABI/AAB,
push commits or publish a release. `tools/prepare_test_build.py` checks expected
upstream text before modifying the disposable copy.

The host sees these files under `$task_root/build`:

- `prepare.log`: checkout, dependency install, hooks, patches, GN generation.
- `compile.log`: full native/Java build output, appended on resume.
- `source-commit.txt`, `submodules.txt`: the inputs actually cloned.
- `prepared`: created only after successful GN generation.
- `artifacts/`: APK, checksum, manifest/ABI report, signature/certificate report,
  source commit, submodule revision and GN args after successful verification.

For a compile failure after preparation, inspect the error, repair the relevant
source, and resume without fetching and rebuilding everything. For Podman:

```sh
podman_task run --rm --userns=keep-id -e TITANIUM_JOBS=2 \
  -v "$repo_root:/input:ro" -v "$task_root/build:/build" \
  localhost/titanium-test-builder \
  bash tools/build-test-apk.sh --resume /build
```

For Docker, use the same `docker run` mounts/image and append
`bash tools/build-test-apk.sh --resume /build`.

Resume compiles the existing disposable source; it does **not** silently pull
new source changes into it or reapply patches. Port each repair both to the
maintained source patch in the feature checkout and to the existing disposable
Chromium tree, and record the resulting diff. Before reporting the final source
commit, commit the maintained repair and refresh provenance to include that
commit plus the applied disposable-tree diff. Re-run affected patch/UI checks.
A new clean build from the repaired commit is the strongest final verification.
Do not relabel an older build as a newer commit without that evidence.

If preparation fails before `prepared` exists, inspect `prepare.log` and repair
that step in the disposable environment. Do not rerun the whole upstream
preparation against a half-patched tree blindly. Preserve useful logs and fixes;
use a new empty build directory if clean preparation is needed.

## Verify and install the test app

The script checks the APK's package and ARM64 ABI with the SDK's `aapt2`, verifies
its signature with `apksigner`, and writes `SHA256SUMS`. Inspect these reports.
Development signing is suitable for this separate test app, not an official
release. Do not use the original browser package or official signing secrets.

The artifact is:

```text
$task_root/build/artifacts/titanium-codex-test-arm64.apk
```

Transfer this APK and its checksum to the Windows PC where the phone is connected,
or connect/authorize the phone on SteamOS and use host ADB. Do not expose ADB over
the network or pass USB devices into the build container just to install it.

```sh
adb devices -l
# Select the authorized Moto G explicitly, especially if more than one device is listed.
adb -s PHONE_SERIAL install -r /path/to/titanium-codex-test-arm64.apk
```

Replace the two placeholders with verified values. The owner has authorized
installing this test app. Never uninstall another browser or clear browser data;
on a signature conflict, diagnose it and preserve the existing installation.
Launch the test app, confirm the separate package, and inspect startup logs for
crashes before calling installation successful.

## Live acceptance checklist

Test normal and incognito tabs, keyboard showing/hiding, gesture navigation
insets and portrait/landscape where possible:

1. Enable Address bar > Bottom. Tap the URL field on a loaded page, type, use a
   suggestion and dismiss the keyboard. The editable field remains above the
   keyboard; suggestions grow upward and stay tappable.
2. Open the tab switcher with 0, 1, 3 and many tabs. Search is at the bottom,
   actions just above it, and short lists/cards stay near the bottom. Search,
   create, switch, close, undo and close-last-tab work. Exercise tab groups too.
3. Switch Grid / Cards in Tabs and tab groups. Cards show wide overlapping
   previews, scroll and animate; Grid remains usable. Check titles, close buttons,
   selected state and accessibility. Check Top mode for regressions.
4. Enable OLED black backgrounds. Check actual background pixels are `#000000`
   in the switcher, cards, omnibox, suggestion area and settings. Accents should
   follow Android's theme, including a theme change; no gold constants.
5. Disable OLED and confirm the saved Light/Dark/System choice returns. Restart
   the app and confirm preferences persist.

Record observed results separately from what needs the owner's hands-on review.
Keep the build available for iteration until they explicitly accept the result.

## Cleanup after the owner accepts the app

First preserve only the final APK/checksum and source evidence that the owner
wants. Push maintained fixes to the fork. Verify the resolved `task_root` is the
exact task-owned directory, has `.titanium-task`, and is neither `/`, the home
directory, the source checkout nor an ancestor of it.

- Podman: inspect `podman_task info` and confirm its storage paths are under the
  verified task directory. Remove this private store's containers and images with
  `podman_task rm --all --force` and `podman_task rmi --all --force`. Remove the
  checked task directory, using this runtime's `unshare` if mapped file ownership
  requires it. Its private storage, container HOME and build disappear.
  **Never run unscoped Podman cleanup, or `podman system reset`** (which can also
  affect machine configuration outside the image store).
- Docker: remove only the recorded builder using
  `docker buildx rm "$builder"` (do not keep its state), then
  `docker image rm "$image"`. Verify that builder's BuildKit container/cache volume
  is gone. Remove the task directory. Do not run global builder/system prune.
- Remove runtime components only if installed solely for this task and unused
  by anything else. Restore any task-specific keep-awake setting.
- The earlier Windows checkout has task-owned source/Gradle caches too; those
  can be removed after acceptance from that PC. They are not on SteamOS.

Do not delete the incremental build merely because compilation succeeds. The
cleanup point requested by the owner is **after they like and accept Titanium**.

## References

- [Chromium Android build requirements](https://chromium.googlesource.com/chromium/src/+/main/docs/android_build_instructions.md)
- [Podman global options / isolated storage](https://docs.podman.io/en/latest/markdown/podman.1.html)
- [Docker Buildx builder removal](https://docs.docker.com/reference/cli/docker/buildx/rm/)
