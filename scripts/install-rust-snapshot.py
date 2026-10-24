#!/usr/bin/env python3
"""Install the bundled exact std source into a NEW private sysroot and rustup alias."""
import argparse
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tarfile

EXPECTED = 'rustc 1.100.0-nightly (0dfb098f3 2026-08-31)'
def output(args):
    return subprocess.check_output(args,text=True).strip()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('archive',type=Path)
    p.add_argument('destination',type=Path)
    p.add_argument('name')
    p.add_argument('--base',default='nightly-2026-09-01')
    a=p.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',a.name) or a.name.startswith(('nightly','stable','beta')) or a.name=='aros-nightly':
        p.error('choose a new private toolchain alias')
    if a.name in {line.split()[0] for line in output(['rustup','toolchain','list']).splitlines()}:
        p.error('toolchain alias already exists; no replacement performed')
    if output(['rustup','run',a.base,'rustc','-V'])!=EXPECTED:p.error('wrong compiler; install the pinned compiler first')
    base=Path(output(['rustup','run',a.base,'rustc','--print','sysroot']))
    dest=a.destination.absolute()
    if dest.exists() or dest.is_symlink():p.error('destination exists; no replacement performed')
    dest.mkdir(parents=True)
    try:
        (dest/'bin').mkdir();(dest/'lib/rustlib/src').mkdir(parents=True)
        for binary in (base/'bin').iterdir():
            args=[str(binary)]
            if binary.name=='rustc':args+=['--sysroot',str(dest)]
            wrapper=dest/'bin'/binary.name
            wrapper.write_text('#!/bin/sh\nexec '+' '.join(map(shlex.quote,args))+' "$@"\n')
            wrapper.chmod(0o755)
        for child in (base/'lib').iterdir():
            if child.name!='rustlib':(dest/'lib'/child.name).symlink_to(child,target_is_directory=child.is_dir())
        for child in (base/'lib/rustlib').iterdir():
            if child.name!='src':(dest/'lib/rustlib'/child.name).symlink_to(child,target_is_directory=child.is_dir())
        with tarfile.open(a.archive) as tar:
            if any(not m.name.startswith('rust/') and m.name!='rust' for m in tar.getmembers()):raise ValueError('unexpected archive root')
            tar.extractall(dest/'lib/rustlib/src',filter='data')
        if not (dest/'lib/rustlib/src/rust/library/std/Cargo.toml').is_file():raise ValueError('std source missing')
        subprocess.run(['rustup','toolchain','link',a.name,str(dest)],check=True)
    except BaseException:
        shutil.rmtree(dest)
        raise
    print(json.dumps({'toolchain':a.name,'compiler':EXPECTED,'sysroot':str(dest)},indent=2))
if __name__=='__main__':main()
