#!/usr/bin/env python3
"""Package an x86_64 v1 CPU build; preserve its exact unstripped counterparts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import icons
import lcconfig
import native_v1
import package


def validate_release_inputs(record, source, manifests):
    if set(record['binaries']) != {'LightCraft', 'lightcraft-cli'}:
        raise package.Failure('release requires both LightCraft and lightcraft-cli')
    if package.sha256((source/'Cargo.lock').read_bytes()) != record['derived_lock_sha256']:
        raise package.Failure('dependency lock differs from the build')
    for name, expected in manifests.items():
        if not (source/name).is_file() or (source/name).read_bytes() != expected:
            raise package.Failure('dependency manifest differs from the build: ' + name)


def dependencies(manifest, cfg):
    command = manifest['command']
    base = command[:command.index('build')]
    prefix = Path(command[0]).parents[1]
    source = Path(command[command.index('--manifest-path') + 1]).parent
    env = dict(os.environ, RUSTC=str(prefix/'bin/rustc'), RUSTDOC=str(prefix/'bin/rustdoc'),
               CARGO_HOME=cfg['cargo_home'], CARGO_TARGET_DIR=str(Path(cfg['build_root'])/'target'))
    target = str(prefix/'share/x86_64-unknown-aros.json')
    def run(args):
        return subprocess.check_output([*base, *args], cwd=source, env=env, text=True)
    metadata = json.loads(run(['metadata', '--locked', '--format-version=1', '--offline', '--no-default-features', '--filter-platform', target]))
    selected = [command[i+1] for i, value in enumerate(command) if value == '-p']
    tree_args = ['tree', '--locked', '--offline', '--no-default-features', '--target', target,
                 '--edges', 'normal,build', '--prefix', 'none', '--format', '{p}']
    for name in selected:
        tree_args += ['-p', name]
    tree = run(tree_args)
    keys = set()
    for line in tree.splitlines():
        match = re.match(r'([^ ]+) v([^ ]+)', line)
        if match:
            keys.add(match.groups())
    forbidden = {name for name, _ in keys} & {'wgpu', 'wgpu-core', 'wgpu-hal', 'eframe', 'glow', 'glutin'}
    if forbidden:
        raise package.Failure('CPU package contains GPU dependencies: ' + str(sorted(forbidden)))
    linked = {}
    packages = []
    for key in sorted(keys):
        matches = [p for p in metadata['packages'] if (p['name'], p['version']) == key]
        if len(matches) != 1:
            raise package.Failure('ambiguous dependency identity: ' + str(key))
        p = matches[0]
        linked[p['id']] = p['manifest_path']
        packages.append(dict(name=p['name'], version=p['version'], license=p.get('license')))
    return linked, source, packages


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('--dist', type=Path, required=True)
    parser.add_argument('--version', default='0.13.0')
    parser.add_argument('--readme', type=Path, required=True)
    parser.add_argument('--reuse-debug', type=Path, help='reuse hash-matched owned debug files for a metadata-only repack')
    args = parser.parse_args()
    cfg = lcconfig.load(['official_sdk', 'aros_sdk', 'aros_gcc', 'cargo_home', 'build_root'])
    for repository in ('lightcraft', 'aros-v1-sdk'):
        subprocess.run([sys.executable, str(package.REPO/'scripts/source.py'), 'verify', '--repository', repository], check=True)
    raw = json.loads((args.build/'manifest.json').read_text())
    if raw['abi'] != 'x86_64 ABIv1' or raw['work_dirty'] or raw['status'] not in ('built-not-run', 'accepted'):
        raise package.Failure('require a clean completed x86_64 v1 build')
    if raw['work_head'] != package.git('rev-parse','HEAD',cwd=package.WORK).decode().strip():
        raise package.Failure('current source differs from the build')
    if '--features' in raw['command']:
        raise package.Failure('optional feature build is not the CPU release profile')
    if '--no-default-features' not in raw['command'] or 'profile.release.lto="fat"' not in raw['command']:
        raise package.Failure('require the CPU-only fat-LTO build')
    installation = native_v1.read_installation(Path(cfg['official_sdk']))
    if installation['generation'] != raw['installation_generation']:
        raise package.Failure('selected SDK differs from the build')
    native = json.loads((Path(installation['native_build'])/'result.json').read_text())
    native_v1.require_nix_mode(installation, native)
    source = Path(raw['command'][raw['command'].index('--manifest-path') + 1]).parent
    names = package.git('ls-tree', '-r', '--name-only', raw['work_head'], cwd=package.WORK).decode().splitlines()
    manifests = {name: package.git('show', raw['work_head'] + ':' + name, cwd=package.WORK)
                 for name in names if Path(name).name == 'Cargo.toml'}
    validate_release_inputs(raw, source, manifests)
    linked, source, package_records = dependencies(raw, cfg)
    validate_release_inputs(raw, source, manifests)
    license_manifest = dict(raw, linked_packages={k:v for k,v in linked.items() if not Path(v).is_relative_to(source)})
    notices, _ = package.third_party(license_manifest)
    notices = notices.replace('linked into LightCraft and lightcraft-cli', 'used to build LightCraft and lightcraft-cli')
    files = {'LightCraft/README.md': (args.readme.read_bytes(), 0o100644)}
    packaged = {}
    debug = args.dist/'debug'
    args.dist.mkdir(parents=True, exist_ok=True)
    if debug.exists():
        raise package.Failure('debug directory exists; use a fresh destination')
    debug.mkdir()
    for name, info in raw['binaries'].items():
        original = (args.build/name).read_bytes()
        if package.sha256(original) != info['sha256'] or original[:6] != b'\x7fELF\x02\x01' or original[7:9] != bytes([15, 1]):
            raise package.Failure('binary identity differs: ' + name)
        data = package.stripped(original, name)
        if b'/Users/' in data or b'/home/' in data:
            raise package.Failure('workstation path remains in ' + name)
        files['LightCraft/'+name] = (data, 0o100755)
        packaged[name] = dict(sha256=package.sha256(data), bytes=len(data), unstripped_sha256=info['sha256'])
        debug_source = args.reuse_debug/(name+'.unstripped') if args.reuse_debug else args.build/name
        if package.sha256(debug_source.read_bytes()) != info['sha256']:
            raise package.Failure('debug source mismatch: ' + name)
        if args.reuse_debug:
            os.link(debug_source, debug/(name+'.unstripped'))
        else:
            shutil.copyfile(debug_source, debug/(name+'.unstripped'))
        if package.sha256((debug/(name+'.unstripped')).read_bytes()) != info['sha256']:
            raise package.Failure('unstripped copy mismatch: ' + name)
    release = json.loads((package.PACKAGING/'release.json').read_text())
    image = package.WORK/release['icon_source'].removeprefix('work:')
    w,h,rows = icons.decode_rgba(image)
    files['LightCraft.info'] = (icons.icon(w,h,rows,icons.ICON_DRAWER,16777216,[]),0o100644)
    files['LightCraft/LightCraft.info'] = (icons.icon(w,h,rows,icons.ICON_TOOL,16777216,['GUI_RENDERER=CPU','IMAGE_COMPUTE=CPU']),0o100644)
    for rel in release['lightcraft_notices']:
        renamed = release.get('notice_renames',{}).get(rel,rel)
        files['LightCraft/Licenses/LightCraft/'+renamed] = ((package.WORK/rel).read_bytes(),0o100644)
    files['LightCraft/Licenses/LightCraft/RENAMED.txt'] = (b'LICENSE-icon.txt is assets/app-icon/LICENSE.txt in ATTRIBUTION.md, renamed to fit a 30-character AmigaDOS name.\n',0o100644)
    files['LightCraft/Licenses/THIRD-PARTY.txt'] = (notices.encode(),0o100644)
    files['LightCraft/Licenses/AROS-NOTICE.txt'] = ((package.PACKAGING/'v1/AROS-NOTICE.txt').read_bytes(),0o100644)
    files['LightCraft/Licenses/AROS-LICENSE.txt'] = ((package.REPO/'work/aros-v1-sdk/LICENSE').read_bytes(),0o100644)
    compiler = Path(next(p for p in installation['inputs'] if p.endswith('/bin/rustc')))
    docs = compiler.parents[1]/'share/doc/rust'
    files['LightCraft/Licenses/Rust/COPYRIGHT-library.html'] = ((docs/'COPYRIGHT-library.html').read_bytes(),0o100644)
    for f in (docs/'licenses').iterdir():
        if f.is_file(): files['LightCraft/Licenses/Rust/licenses/'+f.name] = (f.read_bytes(),0o100644)
    rustc_version = subprocess.check_output([str(compiler),'-Vv'],text=True).strip()
    gcc_version = subprocess.check_output([cfg['aros_gcc'],'--version'],text=True).splitlines()[0]
    series = {}
    for name in ('lightcraft','aros-v1-sdk'):
        root = package.REPO/'patches'/name
        series[name] = {line:package.sha256((root/line).read_bytes()) for line in (root/'series').read_text().splitlines() if line and not line.startswith('#')}
    aliases = [(str(Path(cfg['build_root'])/'src'), '/lightcraft'),
               (str(Path(cfg['build_root'])), '/build'), (cfg['cargo_home'], '/cargo'),
               (installation['native_build'], '/native-std'), (cfg['aros_sdk'], '/sdk'),
               (str(package.REPO), '/port'), (str(Path.home()), '/host')]
    def public_flag(value):
        for original, replacement in sorted(aliases, key=lambda item: len(item[0]), reverse=True):
            value = value.replace(original, replacement)
        return value
    application_flags = next(json.loads(value.split('=',1)[1]) for value in raw['command']
                             if value.startswith('target.x86_64-unknown-aros.rustflags='))
    summary = dict(schema=1, version=args.version, abi=raw['abi'], work_head=raw['work_head'],
                   compiler=rustc_version, gcc=gcc_version, sdk_generation=installation['generation'],
                   path_mode='-nix', panic='abort', lto='fat', stack_bytes=16777216,
                   features=['--no-default-features'], cc_args=installation['cc_args'],
                   rustflags=[public_flag(v) for v in application_flags],
                   std_rustflags=[public_flag(v) for v in native['std_rustflags']],
                   target=json.loads((Path(cfg['official_sdk'])/'share/x86_64-unknown-aros.json').read_text()),
                   renderers={'gui':'CPU','image':'CPU','gpu_backends_compiled':False},
                   source_lock_sha256=raw['source_lock_sha256'], derived_lock_sha256=raw['derived_lock_sha256'],
                   series=series, packaged_binaries=packaged, dependencies=package_records,
                   pthread={k:v for k,v in raw['pthread'].items() if k != 'path'},
                   upstreams=json.loads((package.REPO/'upstreams.json').read_text())['repositories'])
    if '/Users/' in json.dumps(summary): raise package.Failure('private path in public metadata')
    files['LightCraft/BUILD.json'] = ((json.dumps(summary,indent=2)+'\n').encode(),0o100644)
    requirements = [{'type':'library','id':'fd.library','min_version':51},
                    {'type':'library','id':'posixc.library'}, {'type':'library','id':'stdc.library'},
                    {'type':'library','id':'cybergraphics.library'}, {'type':'library','id':'iffparse.library'}]
    app = dict(schema=1,id='lightcraft',version=args.version,targets=[dict(os='aros',arch='x86_64',abi='v1')],
               requires_system=requirements,launch=dict(executable='LightCraft',mode='workbench',working_directory='.'))
    files['LightCraft/application.json'] = ((json.dumps(app,indent=2)+'\n').encode(),0o100644)
    source_text = f'LightCraft {args.version}, x86_64 AROS ABIv1\nhttps://github.com/tomaszstaniak/aros-lightcraft\n\nRebuild: docs/sdk-v1.md and docs/mainline-v1.md in the source recipe.\nThe SDK and runtime proposals are pinned in upstreams.json.\n\n' + ''.join(f"{info['sha256']}  {name}\n" for name,info in packaged.items())
    files['LightCraft/SOURCE.txt'] = (source_text.encode(),0o100644)
    embedded = f'''id = "lightcraft"
version = "{args.version}"
summary = "Photo library and non-destructive RAW editor with CPU rendering"
category = "graphics/edit"
license = "MIT OR Apache-2.0"
kind = "app"
arch = "x86_64"
abi = "v1"
subdir = "LightCraft"
icon = "LightCraft.info"
depends = []
depends_checked = true
post_install_notes = [
  "Requires fd.library 51, posixc.library 0.41 and matching stdc/AROSTCP components. System libraries are not installed by this package.",
  "CPU interface and image processing. GPU backends are not included.",
  "Keep LightCraftData when upgrading; it contains edits and settings.",
  "Optional inference and HEIF are disabled. See README.md for feature details.",
  "Native keyboard and clipboard conversion is limited to Latin-1.",
]
[[requires_system]]
type = "library"
id = "fd.library"
min_version = 51
[[requires_system]]
type = "library"
id = "posixc.library"
[[requires_system]]
type = "library"
id = "stdc.library"
[[requires_system]]
type = "library"
id = "cybergraphics.library"
[[requires_system]]
type = "library"
id = "iffparse.library"
[source]
repository = "https://github.com/tomaszstaniak/aros-lightcraft"
revision = "v{args.version}"
built_with = "x86_64 ABIv1, GCC 10.5.0, Rust 1.99.0-nightly official compiler with AROS std, -nix"
[launch]
executable = "LightCraft"
mode = "workbench"
'''
    files['.arospkg/manifest.toml'] = (embedded.encode(), 0o100644)
    archive = args.dist/f'LightCraft-{args.version}.x86_64-aros-v1.zip'
    if archive.exists(): raise package.Failure('archive exists')
    date = time.gmtime(int(package.git('log','-1','--format=%ct').decode().strip()))[:6]
    with zipfile.ZipFile(archive,'x') as z:
        for name,(data,mode) in sorted(files.items()):
            if any(len(part)>30 for part in name.split('/')): raise package.Failure('AROS filename too long: '+name)
            package.zip_entry(z,name,data,mode,date)
    with zipfile.ZipFile(archive) as z:
        if z.testzip(): raise package.Failure('archive integrity failure')
    sums = [f'{package.sha256(archive.read_bytes())}  {archive.name}']
    sums += [f'{package.sha256(f.read_bytes())}  debug/{f.name}' for f in sorted(debug.iterdir())]
    (args.dist/'SHA256SUMS').write_text('\n'.join(sums)+'\n')
    print(json.dumps(dict(archive=str(archive),sha256=package.sha256(archive.read_bytes()),binaries=packaged),indent=2))

if __name__ == '__main__':
    main()
