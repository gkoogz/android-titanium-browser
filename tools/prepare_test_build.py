#!/usr/bin/env python3
"""Adapt a disposable copy of upstream's build preparation for one test APK."""
import argparse
from pathlib import Path


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"Expected exactly one upstream occurrence: {old!r}")
    return text.replace(old, new, 1)


def prepare(repo):
    args = (repo / 'args.gn').read_text()
    for old, new in [
        ('io.github.jqssun.helium', 'io.github.gkoogz.titanium.test'),
        ('target_cpu = "arm"', 'target_cpu = "arm64"'),
        ('is_official_build = true', 'is_official_build = false'),
        ('symbol_level = 1', 'symbol_level = 0'),
    ]:
        args = replace_once(args, old, new)
    args += '\nuse_thin_lto = false\nchrome_pgo_phase = 0\nuse_remoteexec = false\n'

    script = (repo / 'build.sh').read_text()
    stop = 'autoninja -C out/Default chrome_public_apk'
    if script.splitlines().count(stop) != 1:
        raise ValueError('Upstream first APK build command changed')
    # Preparation only. The caller runs the single ABI build and can resume it.
    script = script[:script.index('\n' + stop + '\n') + 1]
    script = replace_once(script, '#!/bin/bash', '#!/bin/bash\nset -eo pipefail')
    script = replace_once(script, '\nset_keys\n', '\n')
    script = replace_once(script, 'git checkout $VERSION', 'git checkout --detach FETCH_HEAD')
    script = replace_once(script, 'git init\n',
                          'git init\ngit config user.name "Titanium test builder"\n'
                          'git config user.email "titanium-test@localhost"\n')
    script = replace_once(script,
                          'gclient runhooks\n./build/install-build-deps.sh --no-prompt',
                          './build/install-build-deps.sh --no-prompt\ngclient runhooks')
    script += '\ntouch "$TITANIUM_BUILD_ROOT/prepared"\n'
    gclient = replace_once((repo / '.gclient').read_text(),
                           "'checkout_pgo_profiles': True", "'checkout_pgo_profiles': False")

    (repo / 'args.gn').write_text(args, newline='\n')
    (repo / '.gclient').write_text(gclient, newline='\n')
    (repo / 'build_test_prepare.sh').write_text(script, newline='\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=Path, help='Disposable clone; files are edited in place')
    prepare(parser.parse_args().repo.resolve())
