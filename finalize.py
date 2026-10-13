"""Compatibility entry point; the maintained implementation is revise.py."""
from pathlib import Path
import sys,runpy
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
runpy.run_path(str(ROOT/'revise.py'),run_name='__main__')
