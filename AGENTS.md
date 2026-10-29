# Titanium test build handoff

The owner is continuing a browser customization task from a Windows PC on a
SteamOS machine. Read **docs/steam-build-handoff.md** before building. It contains
the requested behavior, current validation limits, container setup, build and
resume commands, device installation, and cleanup boundaries.

The implementation lives on `codex/kiwi-bottom-controls-and-tab-cards` (PR #1).
If this document is present on `main` but the handoff document is absent, fetch
that branch and switch to it after checking for local changes. Preserve existing
work; never reset or clean a checkout to make switching convenient.

Do not run the original `build.sh` directly for this task. Use
`tools/build-test-apk.sh` inside the disposable Ubuntu environment described in
the handoff. The original release workflow builds other architectures, expects
release keys, and publishes releases; it is not the test build route.

Continue through full compilation and fix real build failures. Existing isolated
UI checks are not proof that the full browser compiles or works on the phone.
Record actual commands, source commit, APK checksum, signing certificate, and
device observations. Keep Android accent colors dynamic; never hard-code gold.

Install only the separate `io.github.gkoogz.titanium.test` package. Do not uninstall
or clear another browser. Keep the incremental build until the owner accepts the
app; afterward remove only this task's build, container storage, and caches.
