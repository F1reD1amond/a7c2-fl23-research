"""Load the bundled source layout, retaining native worker asset paths."""
from pathlib import Path
import runpy
import sys
import os
import traceback

try:
    runpy.run_path(str(Path(sys._MEIPASS) / 'desktop.py'), run_name='__main__')
except Exception:
    folder = (Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'A7C2Tools'
              if sys.platform == 'win32' else Path.home() / 'Library/Logs/A7C2Tools')
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'startup-error.log').write_text(traceback.format_exc(), encoding='utf-8')
    if '--offline-self-test' in sys.argv or '--smoke-test' in sys.argv:
        raise SystemExit(2)
    raise
