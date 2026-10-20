"""Build a standalone Windows client; never package the backend or user files."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid


def build_bridge(source, build, environment):
    """Build the channel bridge executable and return its onedir folder."""
    import importlib.util
    bridge_source = source.parent / 'plugins' / 'bridge'
    if not (bridge_source / 'run_bridge.py').is_file():
        raise SystemExit('Bridge plugin sources are missing: plugins/bridge/run_bridge.py')
    dist = build / 'bridge-dist'
    args = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onedir', '--noconsole',
            '--name', 'JunshiBridge', '--distpath', str(dist),
            '--workpath', str(build / 'bridge-work'), '--specpath', str(build),
            '--paths', str(bridge_source)]
    for module in ('httpx', 'playwright', 'playwright.async_api', 'wechatauto', 'wxhook', 'wcferry'):
        try:
            found = importlib.util.find_spec(module.split('.')[0]) is not None
        except (ImportError, ValueError):
            found = False
        if found:
            args += ['--hidden-import', module]
    for package in ('playwright', 'wechatauto'):
        try:
            if importlib.util.find_spec(package) is not None:
                args += ['--collect-all', package]
        except (ImportError, ValueError):
            pass
    args.append(str(bridge_source / 'run_bridge.py'))
    subprocess.run(args, check=True, env=environment)
    folder = dist / 'JunshiBridge'
    if not (folder / 'JunshiBridge.exe').is_file():
        raise SystemExit('Bridge executable was not produced')
    return folder


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--server', default='')
    args = parser.parse_args()
    if sys.platform != 'win32':
        raise SystemExit('Build this Windows package on Windows.')
    from client import Client
    server = Client(args.server).base if args.server else ''
    source = Path(__file__).resolve().parent
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    build = output / ('build-' + uuid.uuid4().hex[:8])
    build.mkdir()
    environment = {key:value for key,value in os.environ.items() if key.upper() not in ('PYTHONPATH','PYTHONHOME')}
    # A venv created from Conda still loads CPython extension dependencies here.
    library = Path(sys.base_prefix)/'Library'/'bin'
    if library.is_dir():
        environment['PATH'] = str(library) + os.pathsep + environment.get('PATH','')
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onedir', '--windowed',
        '--name', 'JunshiPC', '--distpath', str(build/'dist'), '--workpath', str(build/'work'),
        '--specpath', str(build), '--paths', str(source), str(source/'launcher.py')], check=True, env=environment)
    app = build/'dist'/'JunshiPC'
    shutil.copy2(source/'CLIENT_README.txt', app/'浣跨敤璇存槑.txt')
    bridge = build_bridge(source, build, environment)
    shutil.copytree(bridge, app/'JunshiBridge')
    # Ship runtime license notices independently of the source checkout.
    notices = app/'licenses'; notices.mkdir()
    import importlib.metadata
    for package in ('Pillow','pyinstaller'):
        dist=importlib.metadata.distribution(package)
        for item in dist.files or ():
            if 'license' in str(item).lower() or 'copying' in str(item).lower():
                path=Path(dist.locate_file(item))
                if path.is_file(): shutil.copy2(path, notices/(package+'-'+path.name))
    for name in ('LICENSE.txt','LICENSE'):
        path=Path(sys.base_prefix)/name
        if path.is_file(): shutil.copy2(path,notices/('Python-'+name))
    if server:
        (app/'client-config.json').write_text(json.dumps({'server':server}),encoding='utf-8')
    report = build/'smoke.json'
    completed=subprocess.run([str(app/'JunshiPC.exe'),'--self-test',str(report)],timeout=30)
    assert completed.returncode == 0 and json.loads(report.read_text())['frozen'], 'Packaged smoke test failed'
    assert not list(app.rglob('*.sqlite3')) and not list(app.rglob('.env'))
    assert (app/'JunshiBridge'/'JunshiBridge.exe').is_file(), 'Bundled bridge executable missing'
    archive=Path(shutil.make_archive(str(output/'JunshiPC-232-Windows-x64'), 'zip', app.parent, app.name))
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n',encoding='ascii')
    (output/'build-result.json').write_text(json.dumps({'exe':str(app/'JunshiPC.exe'),'zip':str(archive),'sha256':digest,'smoke':'PASS'},indent=2),encoding='utf-8')
    print('Standalone client build and packaged smoke: PASS')
    print(archive)


if __name__ == '__main__':
    main()
