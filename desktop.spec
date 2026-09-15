from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata

root = Path(SPECPATH)
datas = [(str(root / 'app.py'), '.'), (str(root / 'approved-answers.md'), '.'),
         (str(root / 'knowledge-base'), 'knowledge-base'),
         (str(root / 'questionnaires'), 'questionnaires'),
         (str(root / 'DESKTOP_GUIDE.md'), '.')]
binaries = []
hidden = ['workflow', 'semantic', 'commitments', 'secure_settings', 'app_paths',
          'keyring.backends.Windows', 'pystray._win32', 'unittest.mock']
for package in ('streamlit', 'uvicorn', 'google.genai'):
    data, binary, modules = collect_all(package)
    datas += data
    binaries += binary
    hidden += modules
for distribution in ('streamlit', 'google-genai', 'keyring', 'pystray'):
    datas += copy_metadata(distribution, recursive=True)

a = Analysis([str(root / 'desktop_launcher.py')], pathex=[str(root)],
             hookspath=[str(root / 'desktop-hooks')],
             binaries=binaries, datas=datas, hiddenimports=hidden,
             excludes=['matplotlib', 'scipy', 'torch', 'IPython'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='QuestionnaireReview',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='QuestionnaireReview')
