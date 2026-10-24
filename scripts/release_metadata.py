#!/usr/bin/env python3
"""Normalize release metadata while preserving every executable and icon byte."""
import argparse,copy,json,zipfile
from pathlib import Path

def normalize(source, destination):
    with zipfile.ZipFile(source) as old:
        app=json.loads(old.read('LightCraft/application.json'))
        abi=app['targets'][0]['abi']
        if abi not in ('v1','v11'): raise ValueError('unsupported ABI')
        original_version=app['version']
        app['version']='0.13.0'
        changed={}
        for name in ['.arospkg/manifest.toml','LightCraft/SOURCE.txt','LightCraft/README.md']:
            data=old.read(name).decode()
            data=data.replace('0.13.0-aros1','0.13.0').replace('0.13.0-aros2','0.13.0')
            data=data.replace('LightCraft-0.13.0-source.zip',f'LightCraft-0.13.0-source.x86_64-aros-{abi}.zip')
            changed[name]=data.encode()
        changed['LightCraft/application.json']=(json.dumps(app,indent=2)+'\n').encode()
        build=json.loads(old.read('LightCraft/BUILD.json'))
        if 'version' in build:build['version']='0.13.0'
        changed['LightCraft/BUILD.json']=(json.dumps(build,indent=2)+'\n').encode()
        with zipfile.ZipFile(destination,'w') as new:
            for info in old.infolist():
                new.writestr(copy.copy(info),changed.get(info.filename,old.read(info.filename)),compresslevel=9)
        with zipfile.ZipFile(destination) as new:
            assert new.testzip() is None
            assert new.namelist()==old.namelist()
            for name in old.namelist():
                if name not in changed:assert new.read(name)==old.read(name),name
            for name in ['LightCraft/LightCraft','LightCraft/lightcraft-cli','LightCraft.info','LightCraft/LightCraft.info']:
                assert new.read(name)==old.read(name),name
    print(f'{abi}: version {original_version} -> 0.13.0; executables, icons and all other payload files identical')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('destination',type=Path)
    a=p.parse_args();normalize(a.source,a.destination)
