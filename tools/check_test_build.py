#!/usr/bin/env python3
"""Exercise test-only preparation on a temporary upstream copy, without fetching Chromium."""
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from prepare_test_build import prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bash', default='bash')
    options = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='titanium-test-preparation-') as directory:
        repo = Path(directory)
        for name in ['args.gn', 'build.sh', '.gclient']:
            shutil.copyfile(root / name, repo / name)
        prepare(repo)
        args = (repo / 'args.gn').read_text()
        assert 'chrome_public_manifest_package = "io.github.gkoogz.titanium.test"' in args
        assert 'target_cpu = "arm64"' in args
        assert 'is_official_build = false' in args
        assert 'use_thin_lto = false' in args and 'chrome_pgo_phase = 0' in args
        assert 'use_remoteexec = false' in args
        script = (repo / 'build_test_prepare.sh').read_text()
        assert '\nset_keys\n' not in script
        assert 'sign_apk ' not in script and 'sign_aab ' not in script
        assert 'autoninja ' not in script and 'chrome_public_bundle' not in script
        assert 'git checkout --detach FETCH_HEAD' in script
        assert 'source $SCRIPT_DIR/patch.sh' in script
        assert 'git am --whitespace=nowarn --keep-non-patch' in script
        assert script.index('./build/install-build-deps.sh --no-prompt') < script.index('gclient runhooks')
        assert script.index('gn gen out/Default') < script.index('touch "$TITANIUM_BUILD_ROOT/prepared"')
        assert "'checkout_pgo_profiles': False" in (repo / '.gclient').read_text()
        subprocess.run([options.bash, '-n', 'build_test_prepare.sh'], cwd=repo, check=True)
        # A changed upstream assumption must fail instead of producing a partial adapter.
        try:
            prepare(repo)
        except ValueError:
            pass
        else:
            raise AssertionError('Repeated adaptation should fail closed')
    print('Test build preparation checks passed; this is not a full Chromium build.')


if __name__ == '__main__':
    main()
