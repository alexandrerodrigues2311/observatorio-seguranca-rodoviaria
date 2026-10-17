"""Compatibilidade: usa o gerador unificado da apresentação revisada."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name("revisar_apresentacao_visual.py")),run_name="__main__")
